import os
import time
import requests
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

GOOGLE_PLACES_SEARCH_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
# Optional: switch to searchNearby if you have a strict lat/lng query only:
# GOOGLE_PLACES_SEARCH_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"

API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")  # set this in your env

# What we want back (kept small to reduce cost/latency)
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
        "places.websiteUri",
        "places.businessStatus",
    ]
)


class PlaceCandidate(BaseModel):
    place_id: str = Field(alias="id")
    name: str = Field(alias="displayName")
    address: Optional[str] = Field(default=None, alias="formattedAddress")
    lat: Optional[float] = None
    lng: Optional[float] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = Field(default=None, alias="userRatingCount")
    types: List[str] = []
    google_maps_uri: Optional[str] = Field(default=None, alias="googleMapsUri")
    website_uri: Optional[str] = Field(default=None, alias="websiteUri")
    business_status: Optional[str] = Field(default=None, alias="businessStatus")

    @classmethod
    def from_api(cls, p: Dict[str, Any]) -> "PlaceCandidate":
        name = (
            p.get("displayName", {}).get("text")
            if isinstance(p.get("displayName"), dict)
            else p.get("displayName")
        )
        candidate = {
            "id": p.get("id"),
            "displayName": name,
            "formattedAddress": p.get("formattedAddress"),
            "rating": p.get("rating"),
            "userRatingCount": p.get("userRatingCount"),
            "types": p.get("types", []),
            "googleMapsUri": p.get("googleMapsUri"),
            "websiteUri": p.get("websiteUri"),
            "businessStatus": p.get("businessStatus"),
        }
        loc = p.get("location", {})
        if "latitude" in loc and "longitude" in loc:
            candidate["lat"] = loc["latitude"]
            candidate["lng"] = loc["longitude"]
        return cls(**candidate)


def _headers() -> Dict[str, str]:
    if not API_KEY:
        raise RuntimeError("GOOGLE_CLOUD_API_KEY not set")
    return {
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
        "Content-Type": "application/json",
    }


def _search_text_page(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(
        GOOGLE_PLACES_SEARCH_TEXT_URL, headers=_headers(), json=payload, timeout=15
    )
    if resp.status_code == 429:
        # basic backoff & single retry
        time.sleep(1.2)
        resp = requests.post(
            GOOGLE_PLACES_SEARCH_TEXT_URL, headers=_headers(), json=payload, timeout=15
        )
    if not resp.ok:
        raise RuntimeError(f"Places API error {resp.status_code}: {resp.text}")
    return resp.json()


def _parse_radius_m(radius_m) -> Optional[float]:
    """Accept int/float or strings like '5km', '5000m' and return meters as float."""
    if radius_m is None:
        return None
    if isinstance(radius_m, (int, float)):
        return float(radius_m)
    s = str(radius_m).strip().lower()
    if s.endswith("km"):
        return float(s[:-2].strip()) * 1000.0
    if s.endswith("m"):
        return float(s[:-1].strip())
    # raw number as string
    return float(s)


def _build_payload(
    text_query: str,
    lat: Optional[float],
    lng: Optional[float],
    radius_m: Optional[int | float | str],
    open_now: Optional[bool],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "textQuery": text_query,
        "maxResultCount": 20,  # max 20 per page
    }
    if open_now is True:
        payload["openNow"] = True

    # Add a location bias if we have coordinates (helps keep results near the user)
    if lat is not None and lng is not None and radius_m:
        radius_val = _parse_radius_m(radius_m)  # <<--- numeric meters, no 'm'
        payload["locationBias"] = {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_val,  # must be a number, not a string
            }
        }
    return payload

# ...existing code...

def search(intent: Dict[str, Any]) -> List[PlaceCandidate]:
    """
    intent expects keys:
      - queries: List[str]  (or "categories")
      - lat, lng, radius_m (optional)
      - open_now (optional)
      - min_rating (optional)
      - max_results (optional)
    """
    queries = intent.get("queries") or intent.get("categories") or []
    if isinstance(queries, str):
        queries = [queries]
    queries = [q for q in (q.strip() for q in queries) if q]

    lat = intent.get("lat")
    lng = intent.get("lng")
    radius_m = intent.get("radius_m", None)
    open_now = intent.get("open_now", None)
    min_rating = intent.get("min_rating", None)
    max_results = int(intent.get("max_results", 60))  # Increased to allow all queries
    results_per_query = max(10, max_results // len(queries))  # Distribute results across queries

    print(f"🔍 Google Places Search Debug:")
    print(f"   Queries: {queries}")
    print(f"   Location: {lat}, {lng}")
    print(f"   Radius: {radius_m}m")
    print(f"   Max results: {max_results}")
    print(f"   Results per query: {results_per_query}")

    if not queries:
        raise ValueError(
            "intent.queries (or .categories) must contain at least one search term"
        )

    seen: set[str] = set()
    out: List[PlaceCandidate] = []

    for q in queries:
        print(f"\n🔎 Searching for: '{q}'")
        
        # Make the query human-like to improve text search quality
        text_query = q
        if lat is not None and lng is not None:
            # "near me" tends to work well with a location bias
            text_query = f"best {q} near me"

        print(f"   Text query: '{text_query}'")
        payload = _build_payload(text_query, lat, lng, radius_m, open_now)

        # paginate until we hit our cap per query or no nextPageToken
        page_token = None
        query_results = 0
        while query_results < results_per_query:  # Limit per query, not total
            if page_token:
                payload["pageToken"] = page_token
            data = _search_text_page(payload)

            places_in_page = len(data.get("places", []))
            print(f"   📄 Page returned {places_in_page} places")

            for p in data.get("places", []):
                pid = p.get("id")
                if not pid or pid in seen:
                    continue
                cand = PlaceCandidate.from_api(p)

                # Print each candidate
                print(f"   📍 {cand.name} - Types: {cand.types} - Rating: {cand.rating}")

                # filter by rating if configured
                if (
                    (min_rating is not None)
                    and (cand.rating is not None)
                    and (cand.rating < float(min_rating))
                ):
                    print(f"      ❌ Filtered out (rating {cand.rating} < {min_rating})")
                    continue

                out.append(cand)
                seen.add(pid)
                query_results += 1
                if query_results >= results_per_query:
                    break

            if query_results >= results_per_query:
                break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

            # tiny pause; nextPageToken sometimes needs a moment before it becomes valid
            time.sleep(0.5)

        print(f"   ✅ Found {query_results} results for '{q}'")

    print(f"\n📊 Total candidates found: {len(out)}")
    
    # Group by type for summary
    type_counts = {}
    for cand in out:
        for place_type in cand.types:
            type_counts[place_type] = type_counts.get(place_type, 0) + 1
    
    print(f"📈 Candidates by type:")
    for ptype, count in sorted(type_counts.items()):
        print(f"   {ptype}: {count}")

    # Sort results to make LLM selection easier:
    # primary: rating desc, secondary: user_ratings_total desc
    out.sort(key=lambda c: ((c.rating or 0), (c.user_ratings_total or 0)), reverse=True)
    return out