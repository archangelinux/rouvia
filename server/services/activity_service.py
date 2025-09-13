import os
import asyncio
import requests
from dotenv import load_dotenv
from services.luma_scraper import fetch_luma_events, fetch_local_blog_events
from services.scoring_service import activity_scorer
from services.enhanced_scraper import trendiness_checker

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
EVENTBRITE_API_KEY = os.getenv("EVENTBRITE_API_KEY")



def get_city_from_latlon(lat, lon):
    """
    Given latitude and longitude, return the city name using Google Geocoding API.
    If it fails, fallback to 'Waterloo'.
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_API_KEY}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        if not data.get("results"):
            print("[Sidequest] No geocoding results, using fallback city 'Waterloo'")
            return "Waterloo"

        # Look for the 'locality' component
        for component in data["results"][0].get("address_components", []):
            if "locality" in component.get("types", []):
                return component["long_name"]

        # fallback if no locality
        print("[Sidequest] Could not determine city from results, using fallback 'Waterloo'")
        return "Waterloo"

    except Exception as e:
        print(f"[Sidequest] Error fetching city: {e}. Using fallback 'Waterloo'")
        return "Waterloo"

async def fetch_eventbrite_events(lat, lon, radius_km=5):
    """Fetch events from Eventbrite with Cohere interpretation. Returns empty list on failure."""
    if not EVENTBRITE_API_KEY:
        print("[Eventbrite] No API key available, skipping Eventbrite")
        return []
        
    url = f"https://www.eventbriteapi.com/v3/events/search/?location.latitude={lat}&location.longitude={lon}&location.within={radius_km}km"
    headers = {"Authorization": f"Bearer {EVENTBRITE_API_KEY}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        data = res.json()
        events = []
        
        for e in data.get("events", []):
            # Extract raw event data
            event_name = e.get("name", {}).get("text", "Eventbrite Event")
            event_description = e.get("description", {}).get("text", "")
            event_url = e.get("url", "")
            venue_info = e.get("venue", {})
            venue_name = venue_info.get("name", "")
            venue_address = venue_info.get("address", {}).get("localized_address_display", "")
            
            # Combine all text for Cohere analysis
            full_text = f"Event: {event_name}\nDescription: {event_description}\nVenue: {venue_name}\nAddress: {venue_address}\nURL: {event_url}"
            
            # Use enhanced scraper to interpret the event data
            enhanced_data = await enhanced_scraper.scrape_place_details(event_name, f"eventbrite_{e.get('id', '')}", venue_address)
            
            if enhanced_data:
                structured = {
                    "title": event_name,
                    "location": venue_address or venue_name,
                    "start_time": None,  # Eventbrite has complex date handling
                    "duration_hours": enhanced_data.get("duration_hours", 2.0),
                    "cost": enhanced_data.get("cost", 0),
                    "activity_type": enhanced_data.get("activity_type", "entertainment"),
                    "indoor_outdoor": enhanced_data.get("indoor_outdoor", "indoor"),
                    "energy_level": enhanced_data.get("energy_level", 5),
                    "confidence": enhanced_data.get("confidence", 0.8),
                    "description": enhanced_data.get("description", event_description[:200]),
                    "highlights": enhanced_data.get("highlights", "")
                }
            else:
                # Fallback if Cohere fails
                structured = {
                    "title": event_name,
                    "location": venue_address or venue_name,
                    "start_time": None,
                    "duration_hours": 2.0,
                    "cost": 0,
                    "activity_type": "entertainment",
                    "indoor_outdoor": "indoor",
                    "energy_level": 5,
                    "confidence": 0.5,
                    "description": event_description[:200] if event_description else "",
                    "highlights": ""
                }
            
            events.append({
                "raw_name": event_name,
                "place_id": f"eventbrite_{e.get('id', '')}",
                "structured": structured
            })
            
        print(f"[Eventbrite] Found {len(events)} events with Cohere interpretation")
        return events
        
    except Exception as e:
        print(f"[Eventbrite] Failed: {e}")
        return []


def fetch_google_places(lat, lon):
    """
    Fetch places from Google Places API for a given location.
    Returns structured activities with fallback data if API fails.
    """
    print(f"[Google Places] Fetching places for lat={lat}, lon={lon}")
    
    if not GOOGLE_API_KEY:
        print("[Google Places] No API key found, returning fallback data")
        return _get_fallback_activities(lat, lon)
    
    try:
        # Get city name for better search results
        city = get_city_from_latlon(lat, lon)
        print(f"[Google Places] Searching in city: {city}")
        
        activities = []
        
        # Define search queries for different activity types
        search_queries = [
            f"restaurants in {city}",
            f"tourist attractions in {city}",
            f"parks in {city}",
            f"museums in {city}",
            f"shopping centers in {city}",
            f"entertainment venues in {city}",
            f"cafes in {city}",
            f"bars in {city}",
            f"outdoor activities in {city}",
            f"indoor activities in {city}"
        ]
        
        for query in search_queries:
            try:
                # Use NEW Places API (Text Search)
                url = "https://places.googleapis.com/v1/places:searchText"
                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": GOOGLE_API_KEY,
                    "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.types,places.priceLevel,places.currentOpeningHours"
                }
                
                payload = {
                    "textQuery": query,
                    "locationBias": {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lon},
                            "radius": 5000.0  # 5km radius
                        }
                    },
                    "maxResultCount": 10
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                print(f"[Google Places] Query '{query}' returned {len(data.get('places', []))} results")
                
                for place in data.get("places", []):
                    structured_place = _structure_new_google_place(place, city)
                    if structured_place:
                        activities.append(structured_place)
                
            except Exception as e:
                print(f"[Google Places] Error fetching for query '{query}': {e}")
                # Fallback to legacy API if new API fails
                try:
                    legacy_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                    legacy_params = {
                        "query": query,
                        "key": GOOGLE_API_KEY,
                        "fields": "place_id,name,formatted_address,geometry,rating,types,price_level",
                        "location": f"{lat},{lon}",
                        "radius": 5000
                    }
                    
                    legacy_response = requests.get(legacy_url, params=legacy_params, timeout=10)
                    legacy_response.raise_for_status()
                    legacy_data = legacy_response.json()
                    
                    if legacy_data.get("status") == "OK":
                        for place in legacy_data.get("results", []):
                            structured_place = _structure_google_place(place, city)
                            if structured_place:
                                activities.append(structured_place)
                    else:
                        print(f"[Google Places] Legacy API also failed: {legacy_data.get('status')}")
                        
                except Exception as legacy_e:
                    print(f"[Google Places] Legacy API fallback also failed: {legacy_e}")
                continue
        
        print(f"[Google Places] Found {len(activities)} total activities")
        
        # If no activities found, return fallback data
        if not activities:
            print("[Google Places] No activities found, returning fallback data")
            return _get_fallback_activities(lat, lon)
        
        return activities
        
    except Exception as e:
        print(f"[Google Places] Critical error: {e}")
        return _get_fallback_activities(lat, lon)

def _structure_new_google_place(place, city):
    """
    Structure a NEW Google Places API result into our activity format
    """
    try:
        # Extract basic info from new API format
        name = place.get("displayName", {}).get("text", "Unknown")
        place_id = place.get("id", "")
        rating = place.get("rating", 0)
        types = place.get("types", [])
        price_level = place.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
        
        # Convert price level from new API format
        price_mapping = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4
        }
        price_level_num = price_mapping.get(price_level, 2)
        
        # Determine activity type based on Google types
        activity_type = _map_google_types_to_activity_type(types)
        
        # Determine indoor/outdoor
        indoor_outdoor = _determine_indoor_outdoor(types)
        
        # Don't estimate cost - let Cohere handle all pricing intelligently
        cost = 0  # Placeholder, will be overridden by enhanced scraper
        
        # Estimate energy level based on activity type
        energy_level = _estimate_energy_level(activity_type, types)
        
        # Calculate confidence based on rating and relevance
        confidence = _calculate_confidence(rating, types)
        
        # Get formatted address
        formatted_address = place.get("formattedAddress", city)
        
        structured = {
            "title": name,
            "location": formatted_address,
            "start_time": None,  # Would need additional API call for hours
            "duration_hours": _estimate_duration(activity_type),
            "cost": cost,
            "activity_type": activity_type,
            "indoor_outdoor": indoor_outdoor,
            "energy_level": energy_level,
            "confidence": confidence
        }
        
        print(f"[Google Places] Structured (NEW API): {name} -> {activity_type} ({indoor_outdoor}, pricing by Cohere, energy:{energy_level})")
        
        return {
            "raw_name": name,
            "place_id": place_id,
            "structured": structured
        }
        
    except Exception as e:
        print(f"[Google Places] Error structuring new API place {place.get('displayName', {}).get('text', 'Unknown')}: {e}")
        return None

def _structure_google_place(place, city):
    """
    Structure a Google Places result into our activity format
    """
    try:
        # Extract basic info
        name = place.get("name", "Unknown")
        place_id = place.get("place_id", "")
        rating = place.get("rating", 0)
        types = place.get("types", [])
        price_level = place.get("price_level", 0)
        
        # Determine activity type based on Google types
        activity_type = _map_google_types_to_activity_type(types)
        
        # Determine indoor/outdoor
        indoor_outdoor = _determine_indoor_outdoor(types)
        
        # Don't estimate cost - let Cohere handle all pricing intelligently
        cost = 0  # Placeholder, will be overridden by enhanced scraper
        
        # Estimate energy level based on activity type
        energy_level = _estimate_energy_level(activity_type, types)
        
        # Calculate confidence based on rating and relevance
        confidence = _calculate_confidence(rating, types)
        
        structured = {
            "title": name,
            "location": place.get("formatted_address", city),
            "start_time": None,  # Would need additional API call for hours
            "duration_hours": _estimate_duration(activity_type),
            "cost": cost,
            "activity_type": activity_type,
            "indoor_outdoor": indoor_outdoor,
            "energy_level": energy_level,
            "confidence": confidence
        }
        
        print(f"[Google Places] Structured: {name} -> {activity_type} ({indoor_outdoor}, ${cost}, energy:{energy_level})")
        
        return {
            "raw_name": name,
            "place_id": place_id,
            "structured": structured
        }
        
    except Exception as e:
        print(f"[Google Places] Error structuring place {place.get('name', 'Unknown')}: {e}")
        return None

def _map_google_types_to_activity_type(types):
    """Map Google Places types to our activity types"""
    type_mapping = {
        "food": ["restaurant", "food", "meal_takeaway", "cafe", "bar", "bakery"],
        "scenery": ["tourist_attraction", "park", "natural_feature", "zoo", "aquarium"],
        "physical": ["gym", "sports_complex", "stadium", "amusement_park", "bowling_alley"],
        "cultural": ["museum", "art_gallery", "library", "theater", "movie_theater"],
        "shopping": ["shopping_mall", "store", "clothing_store", "electronics_store"],
        "entertainment": ["night_club", "casino", "amusement_park", "aquarium"]
    }
    
    for activity_type, google_types in type_mapping.items():
        if any(gt in types for gt in google_types):
            return activity_type
    
    return "general"

def _determine_indoor_outdoor(types):
    """Determine if activity is indoor or outdoor based on types"""
    outdoor_types = ["park", "natural_feature", "zoo", "stadium", "amusement_park"]
    indoor_types = ["restaurant", "museum", "shopping_mall", "theater", "gym", "bar", "cafe"]
    
    if any(ot in types for ot in outdoor_types):
        return "outdoor"
    elif any(it in types for it in indoor_types):
        return "indoor"
    else:
        return "indoor"  # Default to indoor

def _estimate_cost_from_price_level(price_level, activity_type="general"):
    """Estimate cost in dollars based on Google price level and activity type"""
    # Only scenery/parks should be free, physical activities can have costs
    if activity_type == "scenery":
        return 0
    
    cost_mapping = {
        0: 0,      # Free
        1: 15,     # Inexpensive (was 10)
        2: 35,     # Moderate (was 25) 
        3: 60,     # Expensive (was 50)
        4: 120     # Very Expensive (was 100)
    }
    return cost_mapping.get(price_level, 35)  # Default to moderate

async def enhance_place_data_with_scraper(place_data: dict) -> dict:
    """
    Use enhanced scraper to get better pricing and other data for a place.
    This addresses the issue where all places show as $25.
    """
    try:
        place_name = place_data.get("raw_name", "Unknown")
        place_id = place_data.get("place_id", "")
        location = place_data.get("structured", {}).get("location", "")
        
        # Use enhanced scraper to get better data
        enhanced_data = await enhanced_scraper.scrape_place_details(place_name, place_id, location)
        
        # Update the structured data with enhanced information
        if enhanced_data and place_data.get("structured"):
            structured = place_data["structured"]
            
            # Update with enhanced data if available
            structured["cost"] = enhanced_data.get("cost", structured.get("cost", 25))
            structured["duration_hours"] = enhanced_data.get("duration_hours", structured.get("duration_hours", 1.5))
            structured["activity_type"] = enhanced_data.get("activity_type", structured.get("activity_type", "general"))
            structured["indoor_outdoor"] = enhanced_data.get("indoor_outdoor", structured.get("indoor_outdoor", "mixed"))
            structured["energy_level"] = enhanced_data.get("energy_level", structured.get("energy_level", 5))
            structured["confidence"] = enhanced_data.get("confidence", structured.get("confidence", 0.5))
            
            # Add new fields
            structured["description"] = enhanced_data.get("description", "")
            structured["highlights"] = enhanced_data.get("highlights", "")
            
            print(f"[Activity Service] Enhanced: {place_name} -> ${structured['cost']} ({structured['activity_type']})")
        
        return place_data
        
    except Exception as e:
        print(f"[Activity Service] Enhancement error for {place_data.get('raw_name', 'Unknown')}: {e}")
        return place_data

def _estimate_energy_level(activity_type, types):
    """Estimate energy level (1-10) based on activity type"""
    if activity_type == "physical":
        return 8
    elif activity_type == "scenery" and "park" in types:
        return 6
    elif activity_type == "cultural":
        return 4
    elif activity_type == "food":
        return 3
    elif activity_type == "shopping":
        return 5
    else:
        return 5  # Default moderate energy

def _estimate_duration(activity_type):
    """Estimate duration in hours based on activity type"""
    duration_mapping = {
        "food": 1.5,
        "scenery": 2.0,
        "physical": 1.5,
        "cultural": 2.5,
        "shopping": 2.0,
        "entertainment": 2.0,
        "general": 1.5
    }
    return duration_mapping.get(activity_type, 1.5)

def _calculate_confidence(rating, types):
    """Calculate confidence score based on rating and type relevance"""
    base_confidence = min(rating / 5.0, 1.0) if rating > 0 else 0.5
    
    # Boost confidence for well-defined activity types
    if any(t in ["restaurant", "museum", "park", "tourist_attraction"] for t in types):
        base_confidence += 0.1
    
    return min(base_confidence, 1.0)

def _get_fallback_activities(lat, lon):
    """
    Return fallback activities when APIs fail.
    These are generic activities that should work for most locations.
    """
    print("[Google Places] Using fallback activities")
    
    # Determine if we're in a major city based on coordinates
    city_type = "major_city" if (abs(lat) > 30 and abs(lon) > 30) else "small_city"
    
    fallback_activities = [
        {
            "raw_name": "Local Restaurant",
            "place_id": "fallback_1",
            "structured": {
                "title": "Local Restaurant",
                "location": "Nearby Restaurant",
                "start_time": None,
                "duration_hours": 1.5,
                "cost": 25,
                "activity_type": "food",
                "indoor_outdoor": "indoor",
                "energy_level": 3,
                "confidence": 0.7
            }
        },
        {
            "raw_name": "City Park",
            "place_id": "fallback_2",
            "structured": {
                "title": "City Park",
                "location": "Local Park",
                "start_time": None,
                "duration_hours": 2.0,
                "cost": 0,
                "activity_type": "scenery",
                "indoor_outdoor": "outdoor",
                "energy_level": 6,
                "confidence": 0.8
            }
        },
        {
            "raw_name": "Shopping Center",
            "place_id": "fallback_3",
            "structured": {
                "title": "Shopping Center",
                "location": "Local Shopping Area",
                "start_time": None,
                "duration_hours": 2.0,
                "cost": 50,
                "activity_type": "shopping",
                "indoor_outdoor": "indoor",
                "energy_level": 5,
                "confidence": 0.6
            }
        }
    ]
    
    # Add city-specific activities for major cities
    if city_type == "major_city":
        fallback_activities.extend([
            {
                "raw_name": "Museum",
                "place_id": "fallback_4",
                "structured": {
                    "title": "Local Museum",
                    "location": "City Museum",
                    "start_time": None,
                    "duration_hours": 2.5,
                    "cost": 15,
                    "activity_type": "cultural",
                    "indoor_outdoor": "indoor",
                    "energy_level": 4,
                    "confidence": 0.75
                }
            },
            {
                "raw_name": "Entertainment Venue",
                "place_id": "fallback_5",
                "structured": {
                    "title": "Entertainment Venue",
                    "location": "Local Entertainment",
                    "start_time": None,
                    "duration_hours": 2.0,
                    "cost": 30,
                    "activity_type": "entertainment",
                    "indoor_outdoor": "indoor",
                    "energy_level": 7,
                    "confidence": 0.65
                }
            }
        ])
    
    return fallback_activities


async def fetch_all_activities(lat, lon):
    """Fetch all activities safely with comprehensive logging."""
    print(f"[Activity Service] Starting fetch_all_activities for lat={lat}, lon={lon}")
    candidates = []

    # Get city name
    city = get_city_from_latlon(lat, lon)
    print(f"[Activity Service] Determined city: {city}")

    # Fetch from Google Places
    if city:
        print("[Activity Service] Fetching from Google Places...")
        google_activities = fetch_google_places(lat, lon)
        candidates.extend(google_activities)
        print(f"[Activity Service] Google Places returned {len(google_activities)} activities")
    else:
        print("[Activity Service] Could not determine city. Skipping Google sources.")

    # Fetch from Eventbrite (optional)
    print("[Activity Service] Fetching from Eventbrite...")
    eventbrite_activities = await fetch_eventbrite_events(lat, lon, radius_km=5)
    candidates.extend(eventbrite_activities)
    print(f"[Activity Service] Eventbrite returned {len(eventbrite_activities)} activities")

    # Fetch from Luma (real event data)
    print("[Activity Service] Fetching from Luma...")
    luma_activities = fetch_luma_events(city, lat, lon)
    candidates.extend(luma_activities)
    print(f"[Activity Service] Luma returned {len(luma_activities)} activities")

    # Fetch from local blogs (real event data)
    print("[Activity Service] Fetching from local blogs...")
    blog_activities = fetch_local_blog_events(city, lat, lon)
    candidates.extend(blog_activities)
    print(f"[Activity Service] Local blogs returned {len(blog_activities)} activities")

    print(f"[Activity Service] Total candidates found: {len(candidates)}")
    
    # Enhance ALL activities with better scraping using Cohere
    # This addresses the $25 issue by using Cohere multimodal analysis for realistic pricing
    enhanced_candidates = []
    
    print(f"[Activity Service] Enhancing ALL {len(candidates)} activities with Cohere analysis...")
    
    for i, candidate in enumerate(candidates):
        # Use enhanced scraper for ALL activities to get realistic pricing
        enhanced_candidate = await enhance_place_data_with_scraper(candidate)
        enhanced_candidates.append(enhanced_candidate)
        
        # Log progress every 10 activities
        if (i + 1) % 10 == 0:
            print(f"[Activity Service] Enhanced {i + 1}/{len(candidates)} activities...")
    
    # Log summary of activity types and costs
    activity_types = {}
    cost_distribution = {}
    for candidate in enhanced_candidates:
        structured = candidate.get("structured", {})
        activity_type = structured.get("activity_type", "unknown")
        cost = structured.get("cost", 0)
        
        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        cost_distribution[cost] = cost_distribution.get(cost, 0) + 1
    
    print(f"[Activity Service] Activity type breakdown: {activity_types}")
    print(f"[Activity Service] Cost distribution: {cost_distribution}")

    return enhanced_candidates

async def fetch_activities_with_scoring(lat: float, lon: float, interests: list, budget: float, travel_distance: float = 5):
    """
    OPTIMIZED APPROACH: Get 20 places per interest, then select best ones.
    Phase 1: Get 20 places per interest from Google Places (reliable approach)
    Phase 2: Calculate base scores (fast, no API calls)
    Phase 3: Check trendiness for top candidates only (selective Cohere)
    Phase 4: Return best weighted combination
    """
    print(f"[Activity Service] OPTIMIZED APPROACH: Fetching 20 places per interest")
    
    # Phase 1: Get activities per interest (reliable approach)
    all_activities = []
    
    for interest in interests:
        print(f"[Activity Service] Fetching places for interest: {interest}")
        interest_activities = fetch_google_places_by_interest(lat, lon, interest, limit=20)
        all_activities.extend(interest_activities)
    
    print(f"[Activity Service] Phase 1 complete: {len(all_activities)} total activities")
    
    # Phase 2: Calculate base scores (fast, no API calls)
    scored_activities = activity_scorer.calculate_base_scores(
        all_activities, lat, lon, budget
    )
    
    # Phase 3: Select top candidates for trendiness check (minimal Cohere calls)
    top_candidates = activity_scorer.select_top_candidates(scored_activities, per_category=2)  # Reduced from 5 to 2
    print(f"[Activity Service] Phase 2 complete: {len(top_candidates)} candidates for trendiness check")
    
    # Phase 4: Check trendiness for top candidates only (with timeout)
    trendiness_data = {}
    for candidate in top_candidates:
        place_name = candidate.get("name", "")
        location = candidate.get("location", "")
        try:
            # Add timeout to prevent hanging
            trendiness = await asyncio.wait_for(
                trendiness_checker.check_trendiness(place_name, location), 
                timeout=5.0  # 5 second timeout
            )
            trendiness_data[place_name.lower()] = trendiness
        except asyncio.TimeoutError:
            print(f"[Activity Service] Trendiness check timeout for {place_name}, using default score")
            trendiness_data[place_name.lower()] = 0.5  # Default neutral score
        except Exception as e:
            print(f"[Activity Service] Trendiness check error for {place_name}: {e}, using default score")
            trendiness_data[place_name.lower()] = 0.5  # Default neutral score
    
    # Phase 5: Apply trendiness boost and get final scores
    final_activities = activity_scorer.apply_trendiness_boost(scored_activities, trendiness_data)
    
    # Sort by final score and return
    final_activities.sort(key=lambda x: x["final_score"], reverse=True)
    
    print(f"[Activity Service] NEW APPROACH complete: {len(final_activities)} activities with final scores")
    return final_activities

def _get_google_places_type_for_interest(interest: str) -> str:
    """
    Select the best Google Places type for an interest using simple mapping
    """
    # Simple, reliable mapping
    type_mapping = {
        "meals": "restaurant",
        "bites": "cafe", 
        "entertainment": "movie_theater",
        "events": "amusement_park",
        "scenery": "park",
        "culture": "museum",
        "shopping": "shopping_mall",
        "physical_activity": "gym"
    }
    
    selected_type = type_mapping.get(interest, "point_of_interest")
    print(f"[Google Places] Selected '{selected_type}' for interest '{interest}'")
    return selected_type

def fetch_nearby_places_bulk(lat: float, lon: float, limit: int = 100):
    """Fetch nearby places in bulk, then categorize by interest"""
    try:
        # Use the new Places API (New) format for bulk search
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.location,places.rating,places.types,places.priceLevel,places.id"
        }
        data = {
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": 5000.0  # 5km radius in meters
                }
            },
            "maxResultCount": limit,
            "includedTypes": ["restaurant", "cafe", "park", "museum", "amusement_park", "shopping_mall", "gym", "tourist_attraction"]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code != 200:
            print(f"[Google Places] Bulk API Error {response.status_code}: {response.text}")
            return []
            
        api_data = response.json()
        
        print(f"[Google Places] Bulk API Response status: {response.status_code}")
        print(f"[Google Places] Bulk API Response places count: {len(api_data.get('places', []))}")
        
        activities = []
        places = api_data.get("places", [])
        for place in places[:limit]:
            structured_activity = _structure_google_place_bulk(place)
            if structured_activity:
                # Wrap in the format expected by scoring service
                activity = {
                    "structured": structured_activity,
                    "raw_name": structured_activity.get("name", ""),
                    "place_id": structured_activity.get("place_id", "")
                }
                activities.append(activity)
        
        print(f"[Google Places] Bulk fetch found {len(activities)} places")
        return activities
        
    except Exception as e:
        print(f"[Google Places] Error in bulk fetch: {e}")
        return []

def fetch_google_places_by_interest(lat: float, lon: float, interest: str, limit: int = 15):
    """Fetch Google Places activities for a specific interest category"""
    try:
        # Use flexible Google Places types based on interest
        search_type = _get_google_places_type_for_interest(interest)
        
        # Use the new Places API (New) format
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.location,places.rating,places.types,places.priceLevel,places.id"
        }
        data = {
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": 5000.0  # 5km radius in meters
                }
            },
            "includedTypes": [search_type],
            "maxResultCount": limit
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        api_data = response.json()
        
        print(f"[Google Places] API Response status: {response.status_code}")
        print(f"[Google Places] API Response places count: {len(api_data.get('places', []))}")
        
        activities = []
        places = api_data.get("places", [])
        for place in places[:limit]:
            structured_activity = _structure_google_place_new_api(place, interest, search_type)
            if structured_activity:
                # Wrap in the format expected by scoring service
                activity = {
                    "structured": structured_activity,
                    "raw_name": structured_activity.get("name", ""),
                    "place_id": structured_activity.get("place_id", "")
                }
                activities.append(activity)
        
        print(f"[Google Places] Found {len(activities)} places for {interest}")
        return activities
        
    except Exception as e:
        print(f"[Google Places] Error fetching {interest}: {e}")
        return []

def _structure_google_place_bulk(place: dict) -> dict:
    """Structure Google Places data from bulk API and categorize by interest"""
    try:
        name = place.get("displayName", {}).get("text", "")
        place_id = place.get("id", "")
        rating = place.get("rating", 0)
        types = place.get("types", [])
        
        # Get coordinates
        location = place.get("location", {})
        lat = location.get("latitude", 0)
        lon = location.get("longitude", 0)
        
        # Categorize by Google Places types
        activity_type = _categorize_by_google_types(types)
        
        # Simple cost estimation based on priceLevel
        price_level = place.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
        cost_mapping = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 15,
            "PRICE_LEVEL_MODERATE": 30,
            "PRICE_LEVEL_EXPENSIVE": 60,
            "PRICE_LEVEL_VERY_EXPENSIVE": 100
        }
        cost = cost_mapping.get(price_level, 25)
        
        # Simple indoor/outdoor based on type
        indoor_outdoor = "outdoor" if any(t in ["park", "natural_feature"] for t in types) else "indoor"
        
        # Simple duration estimation - max 2 hours per activity
        duration_hours = 2.0 if activity_type in ["meals"] else 1.5
        
        # Simple energy level
        energy_level = 7 if activity_type == "physical_activity" else 5
        
        structured = {
            "title": name,
            "name": name,
            "location": f"{lat},{lon}",
            "lat": lat,
            "lon": lon,
            "start_time": None,
            "duration_hours": duration_hours,
            "cost": cost,
            "activity_type": activity_type,
            "indoor_outdoor": indoor_outdoor,
            "energy_level": energy_level,
            "confidence": 0.8,
            "description": f"{activity_type.title()} activity at {name}",
            "highlights": f"Rating: {rating}/5" if rating > 0 else "Popular local spot",
            "place_id": place_id,
            "raw_name": name,
            "rating": rating,
            "types": types
        }
        
        return structured
        
    except Exception as e:
        print(f"[Google Places] Error structuring bulk place: {e}")
        return None

def _categorize_by_google_types(types: list) -> str:
    """Categorize Google Places types into our interest categories - more flexible"""
    # More flexible categorization
    if any(t in ["restaurant", "meal_takeaway", "meal_delivery", "food"] for t in types):
        return "meals"
    elif any(t in ["cafe", "bakery", "snack"] for t in types):
        return "bites"
    elif any(t in ["park", "natural_feature", "tourist_attraction", "landmark"] for t in types):
        return "scenery"
    elif any(t in ["museum", "art_gallery", "library", "cultural"] for t in types):
        return "culture"
    elif any(t in ["movie_theater", "night_club", "bar", "club", "show"] for t in types):
        return "entertainment"
    elif any(t in ["shopping_mall", "store", "market", "retail"] for t in types):
        return "shopping"
    elif any(t in ["gym", "sports_complex", "fitness_center", "stadium"] for t in types):
        return "physical_activity"
    elif any(t in ["amusement_park", "event", "festival"] for t in types):
        return "events"
    else:
        return "entertainment"  # Default fallback

def _structure_google_place_new_api(place: dict, interest: str, search_type: str) -> dict:
    """Structure Google Places data from new API format"""
    try:
        name = place.get("displayName", {}).get("text", "")
        place_id = place.get("id", "")
        rating = place.get("rating", 0)
        types = place.get("types", [])
        
        # Get coordinates
        location = place.get("location", {})
        lat = location.get("latitude", 0)
        lon = location.get("longitude", 0)
        
        # Map Google Places types to our activity types
        type_mapping = {
            "restaurant": "meals",
            "cafe": "bites", 
            "park": "scenery",
            "museum": "culture",
            "amusement_park": "entertainment",
            "shopping_mall": "shopping",
            "gym": "physical_activity"
        }
        
        # Get the Google Places type from the search_type
        google_type = search_type
        activity_type = type_mapping.get(google_type, interest)  # Fallback to interest
        
        # Simple cost estimation based on priceLevel
        price_level = place.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED")
        cost_mapping = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 15,
            "PRICE_LEVEL_MODERATE": 30,
            "PRICE_LEVEL_EXPENSIVE": 60,
            "PRICE_LEVEL_VERY_EXPENSIVE": 100
        }
        cost = cost_mapping.get(price_level, 25)
        
        # Simple indoor/outdoor based on interest
        indoor_outdoor = "outdoor" if interest in ["scenery", "physical_activity"] else "indoor"
        
        # Simple duration estimation - max 2 hours per activity
        duration_hours = 2.0 if interest in ["meals"] else 1.5
        
        # Simple energy level
        energy_level = 7 if interest == "physical_activity" else 5
        
        structured = {
            "title": name,
            "name": name,  # Add name field for scoring service
            "location": f"{lat},{lon}",
            "lat": lat,  # Add lat field for scoring service
            "lon": lon,  # Add lon field for scoring service
            "start_time": None,
            "duration_hours": duration_hours,
            "cost": cost,
            "activity_type": activity_type,
            "indoor_outdoor": indoor_outdoor,
            "energy_level": energy_level,
            "confidence": 0.8,
            "description": f"{interest.title()} activity at {name}",
            "highlights": f"Rating: {rating}/5" if rating > 0 else "Popular local spot",
            "place_id": place_id,
            "raw_name": name,
            "rating": rating,
            "types": types
        }
        
        return structured
        
    except Exception as e:
        print(f"[Google Places] Error structuring place: {e}")
        return None

def _structure_google_place_fast(place: dict, interest: str) -> dict:
    """Fast structuring of Google Places data without Cohere calls"""
    try:
        name = place.get("name", "")
        place_id = place.get("place_id", "")
        rating = place.get("rating", 0)
        types = place.get("types", [])
        
        # Get coordinates
        geometry = place.get("geometry", {})
        location = geometry.get("location", {})
        lat = location.get("lat", 0)
        lon = location.get("lng", 0)
        
        # Simple activity type mapping
        activity_type = interest  # Use the interest directly
        
        # Simple cost estimation (will be overridden by scoring)
        cost = 25  # Default, scoring will handle this better
        
        # Simple indoor/outdoor
        indoor_outdoor = "outdoor" if "park" in types or "natural" in types else "indoor"
        
        return {
            "name": name,
            "place_id": place_id,
            "lat": lat,
            "lon": lon,
            "rating": rating,
            "cost": cost,
            "activity_type": activity_type,
            "indoor_outdoor": indoor_outdoor,
            "location": f"{lat},{lon}",
            "types": types
        }
        
    except Exception as e:
        print(f"[Google Places] Error structuring place: {e}")
        return None
