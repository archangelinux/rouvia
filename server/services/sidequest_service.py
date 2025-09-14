"""
Structured sidequest service following specific rules for itinerary generation
"""
import asyncio
from services.activity_service import fetch_activities_with_scoring
from services.mongo import activities_col
from services.structured_itinerary_generator import generate_structured_itinerary
from services.user_profile_service import get_or_create_user_profile
from schemas.sidequest import INTEREST_CATEGORIES


async def fetch_and_prepare_sidequests(
    lat: float,
    lon: float,
    travel_distance: float,
    start_time: str,
    end_time: str,
    budget: float = None,
    interests: list = None,
    energy: int = 5,
    indoor_outdoor: str = None,
    user_id: str = None
):
    """
    Fetch activities and generate structured itinerary following specific rules:
    1. One location per interest category
    2. Max 3 meals/day, 2 meals/half day  
    3. At least one unvisited place
    4. Prioritize meals + entertainment over meals + bites when time is short
    5. Spread food throughout the day
    """
    print(f"[Sidequest] Starting structured fetch for lat={lat}, lon={lon}")
    print(f"[Sidequest] Time: {start_time} to {end_time}")
    print(f"[Sidequest] Filters: budget={budget}, interests={interests}, energy={energy}, indoor_outdoor={indoor_outdoor}")
    
    # Validate interests
    if interests:
        valid_interests = [interest for interest in interests if interest in INTEREST_CATEGORIES]
        if not valid_interests:
            print("[Sidequest] No valid interests provided, using default: entertainment")
            valid_interests = ["entertainment"]
    else:
        print("[Sidequest] No interests provided, using default: entertainment")
        valid_interests = ["entertainment"]
    
    # Get or create user profile
    user_profile = get_or_create_user_profile(user_id)
    
    # Fetch all activities
    candidates = await fetch_activities_with_scoring(lat, lon, interests, budget, travel_distance)
    print(f"[Sidequest] Found {len(candidates)} candidate activities")

    if not candidates:
        print("[Sidequest] No candidates found, returning empty list")
        return {
            "itinerary": [],
            "total_duration": 0,
            "total_cost": 0,
            "summary": "No activities found in the area",
            "metadata": {
                "activities_considered": 0,
                "activities_selected": 0,
                "activities_in_itinerary": 0,
                "interests_covered": [],
                "unvisited_places": 0
            }
        }
    
    # Cache activities and prepare structured data
    structured_activities = []
    for i, candidate in enumerate(candidates):
        print(f"[Sidequest] Processing candidate {i+1}/{len(candidates)}: {candidate.get('raw_name', 'Unknown')}")
        
        place_id = candidate.get("place_id", f"unknown_{i}")
        cached = activities_col.find_one({"place_id": place_id})
        
        if cached:
            activity = cached["structured"]
            print(f"[Sidequest] Using cached activity: {activity.get('title', 'Unknown')}")
        else:
            activity = candidate.get("structured", {})
            if activity:
                activities_col.insert_one({"place_id": place_id, "structured": activity})
                print(f"[Sidequest] Cached new activity: {activity.get('title', 'Unknown')}")
            else:
                print(f"[Sidequest] No structured data for candidate: {candidate.get('raw_name', 'Unknown')}")
                continue
        
        # Ensure coordinates are present
        if not activity.get("lat") or not activity.get("lon"):
            print(f"[Sidequest] Warning: Missing coordinates for {activity.get('title', 'Unknown')}, using fallback")
            activity["lat"] = lat + (0.001 * i)  # Small offset as fallback
            activity["lon"] = lon + (0.001 * i)
        
        # Add metadata for structured processing
        activity["place_id"] = place_id
        activity["raw_name"] = candidate.get("raw_name", "Unknown")
        activity["is_new_place"] = True  # Will be filtered by user profile service
        
        # Wrap activity in the expected format for structured itinerary generator
        wrapped_activity = {
            "structured": activity,
            "raw_name": candidate.get("raw_name", "Unknown"),
            "place_id": place_id
        }
        
        structured_activities.append(wrapped_activity)
    
    print(f"[Sidequest] Prepared {len(structured_activities)} structured activities")
    
    # Generate structured itinerary using new rules
    itinerary_result = generate_structured_itinerary(
        activities=structured_activities,
        start_time=start_time,
        end_time=end_time,
        interests=valid_interests,
        user_id=user_id,
        budget=budget,
        energy=energy,
        indoor_outdoor=indoor_outdoor
    )
    
    # Ensure all activities in the itinerary have lat/lon coordinates
    for activity in itinerary_result.get("itinerary", []):
        if not activity.get("lat") or not activity.get("lon"):
            print(f"[Sidequest] Warning: Activity {activity.get('title', 'Unknown')} missing coordinates")
            activity["lat"] = lat
            activity["lon"] = lon
    
    print(f"[Sidequest] Generated structured itinerary with {len(itinerary_result['itinerary'])} activities")
    print(f"[Sidequest] Summary: {itinerary_result['summary']}")
    
    return itinerary_result


# Legacy function for backward compatibility
async def fetch_and_prepare_sidequests_legacy(
    lat: float,
    lon: float,
    travel_distance: float,
    available_time: float,
    budget: float = None,
    interests: list = None,
    energy: int = 5,
    indoor_outdoor: str = None
):
    """
    Legacy function that converts old parameters to new structured format
    """
    # Convert available_time to start_time and end_time
    start_time = "10:00"  # Default start
    end_time = f"{10 + int(available_time):02d}:00"  # Default end
    
    return await fetch_and_prepare_sidequests(
        lat=lat,
        lon=lon,
        travel_distance=travel_distance,
        start_time=start_time,
        end_time=end_time,
        budget=budget,
        interests=interests,
        energy=energy,
        indoor_outdoor=indoor_outdoor,
        user_id="default_test_user"
    )