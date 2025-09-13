"""
User profile service for tracking visited places and preferences
"""
from typing import List, Dict, Any, Optional
from services.mongo import user_profiles_col
from datetime import datetime
import json

def get_or_create_user_profile(user_id: str = None) -> Dict[str, Any]:
    """
    Get user profile or create a default one for testing
    """
    if not user_id:
        user_id = "default_test_user"
    
    # Try to get existing profile
    profile = user_profiles_col.find_one({"user_id": user_id})
    
    if not profile:
        # Create default test profile with some visited places
        default_profile = {
            "user_id": user_id,
            "visited_places": [
                {
                    "place_name": "Royal Ontario Museum",
                    "place_id": "rom_museum_toronto",
                    "activity_type": "entertainment",
                    "visited_date": "2024-01-15",
                    "location": "Toronto, ON"
                },
                {
                    "place_name": "Tim Hortons",
                    "place_id": "tim_hortons_waterloo",
                    "activity_type": "bites",
                    "visited_date": "2024-01-20",
                    "location": "Waterloo, ON"
                }
            ],
            "preferences": {
                "favorite_cuisines": ["italian", "asian"],
                "budget_range": "moderate",
                "energy_level": 5
            },
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        user_profiles_col.insert_one(default_profile)
        print(f"[User Profile] Created default profile for user: {user_id}")
        return default_profile
    
    print(f"[User Profile] Retrieved profile for user: {user_id}")
    return profile

def add_visited_place(user_id: str, place_name: str, place_id: str, activity_type: str, location: str):
    """
    Add a place to user's visited places
    """
    visited_place = {
        "place_name": place_name,
        "place_id": place_id,
        "activity_type": activity_type,
        "visited_date": datetime.now().isoformat(),
        "location": location
    }
    
    user_profiles_col.update_one(
        {"user_id": user_id},
        {
            "$push": {"visited_places": visited_place},
            "$set": {"last_updated": datetime.now().isoformat()}
        }
    )
    
    print(f"[User Profile] Added visited place: {place_name} for user: {user_id}")

def get_visited_places(user_id: str) -> List[Dict[str, Any]]:
    """
    Get list of places user has visited
    """
    profile = get_or_create_user_profile(user_id)
    return profile.get("visited_places", [])

def has_visited_place(user_id: str, place_name: str) -> bool:
    """
    Check if user has visited a specific place
    """
    visited_places = get_visited_places(user_id)
    return any(place["place_name"].lower() == place_name.lower() for place in visited_places)

def get_visited_place_ids(user_id: str) -> List[str]:
    """
    Get list of place IDs user has visited
    """
    visited_places = get_visited_places(user_id)
    return [place["place_id"] for place in visited_places]

def filter_unvisited_activities(activities: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
    """
    Filter out activities that user has already visited
    """
    visited_place_ids = get_visited_place_ids(user_id)
    unvisited = []
    
    for activity in activities:
        place_id = activity.get("place_id", "")
        place_name = activity.get("raw_name", "")
        
        # Skip if user has visited this place
        if place_id in visited_place_ids or has_visited_place(user_id, place_name):
            print(f"[User Profile] Skipping visited place: {place_name}")
            continue
            
        unvisited.append(activity)
    
    print(f"[User Profile] Filtered {len(activities)} activities to {len(unvisited)} unvisited activities")
    return unvisited
