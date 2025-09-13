# server/schemas/places.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ---- LLM → Places search intent ----
class SearchIntent(BaseModel):
    # e.g., ["ice cream", "scenic lookout", "coffee"]
    queries: List[str]

    # optional user context / constraints
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_m: Optional[int] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None
    max_results: Optional[int] = 40

    # optional extras if your LLM provides them
    price_levels: Optional[List[int]] = None  # 0..4 (Google)
    # future: wheelchair_accessible, kid_friendly, etc.


# ---- Place candidate (normalized for your app/LLM) ----
class PlaceCandidate(BaseModel):
    place_id: str = Field(..., description="Google Places 'id'")
    name: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    types: List[str] = []
    google_maps_uri: Optional[str] = None
    website_uri: Optional[str] = None
    business_status: Optional[
        Literal["OPERATIONAL", "CLOSED_TEMPORARILY", "CLOSED_PERMANENTLY"]
    ] = None


# ---- Wrapper response for Step 3 output → Step 4 input ----
class PlacesCandidatesResponse(BaseModel):
    source: Literal["google_places_v1"] = "google_places_v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    intent: SearchIntent
    # flat list across all queries (you can also keep per-query buckets if you prefer)
    candidates: List[PlaceCandidate]


# ---- (Optional) A minimal "stop" model if you want LLM to return chosen stops in Step 4 ----
class SelectedStop(BaseModel):
    place_id: str
    name: str
    lat: float
    lng: float
    # optional scheduling hints for your route optimizer
    stay_minutes: Optional[int] = None
    earliest_arrival_iso: Optional[str] = None
    latest_departure_iso: Optional[str] = None
