"""
User profile service for tracking visited places and preferences
Enhanced to support Auth0 integration
"""
from typing import List, Dict, Any, Optional
from services.mongo import user_profiles_col
from datetime import datetime
import json
import hashlib

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

# Auth0 Integration Functions

def create_or_update_auth0_user_profile(
    auth0_user_id: str, 
    email: str, 
    name: str = None, 
    nickname: str = None,
    picture: str = None,
    given_name: str = None,
    family_name: str = None
) -> Dict[str, Any]:
    """
    Create or update user profile from Auth0 data
    """
    # Check if user already exists
    existing_profile = user_profiles_col.find_one({"auth0_user_id": auth0_user_id})
    
    current_time = datetime.now().isoformat()
    
    if existing_profile:
        # Update existing profile with Auth0 data
        update_data = {
            "email": email,
            "last_login": current_time,
            "last_updated": current_time
        }
        
        # Add optional fields if provided
        if name:
            update_data["name"] = name
        if nickname:
            update_data["nickname"] = nickname
        if picture:
            update_data["picture"] = picture
        if given_name:
            update_data["given_name"] = given_name
        if family_name:
            update_data["family_name"] = family_name
        
        # Ensure keywords field exists for existing users
        if "keywords" not in existing_profile:
            update_data["keywords"] = {}
            print(f"[User Profile] Added missing keywords field for existing user: {auth0_user_id}")
        
        user_profiles_col.update_one(
            {"auth0_user_id": auth0_user_id},
            {"$set": update_data}
        )
        
        print(f"[User Profile] Updated Auth0 profile for user: {auth0_user_id}")
        return user_profiles_col.find_one({"auth0_user_id": auth0_user_id})
    
    else:
        # Create new profile
        new_profile = {
            "auth0_user_id": auth0_user_id,
            "email": email,
            "name": name,
            "nickname": nickname,
            "picture": picture,
            "given_name": given_name,
            "family_name": family_name,
            "keywords": {},  # JSON field for keyword -> address mapping
            "visited_places": [],
            "preferences": {
                "favorite_cuisines": [],
                "budget_range": "moderate",
                "energy_level": 5
            },
            "created_at": current_time,
            "last_login": current_time,
            "last_updated": current_time
        }
        
        user_profiles_col.insert_one(new_profile)
        print(f"[User Profile] Created new Auth0 profile for user: {auth0_user_id}")
        return new_profile

def add_keyword_location(auth0_user_id: str, keyword: str, location_data: Dict[str, Any]):
    """
    Add or update a keyword -> location mapping
    
    location_data should contain:
    - name: string (location name)
    - address: string (full address)
    - lat: float (latitude)
    - lng: float (longitude)
    - place_id: string (optional, for Google Places)
    """
    location_entry = {
        "name": location_data.get("name", keyword),
        "address": location_data["address"],
        "lat": location_data["lat"],
        "lng": location_data["lng"],
        "place_id": location_data.get("place_id"),
        "added_at": datetime.now().isoformat()
    }
    
    user_profiles_col.update_one(
        {"auth0_user_id": auth0_user_id},
        {
            "$set": {
                f"keywords.{keyword}": location_entry,
                "last_updated": datetime.now().isoformat()
            }
        }
    )
    
    print(f"[User Profile] Added keyword '{keyword}' for user: {auth0_user_id}")

def get_user_keywords(auth0_user_id: str) -> Dict[str, Any]:
    """
    Get all keyword mappings for a user
    """
    profile = user_profiles_col.find_one({"auth0_user_id": auth0_user_id})
    if profile:
        return profile.get("keywords", {})
    return {}

def get_user_profile_by_auth0_id(auth0_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile by Auth0 user ID
    """
    return user_profiles_col.find_one({"auth0_user_id": auth0_user_id})

def delete_keyword(auth0_user_id: str, keyword: str):
    """
    Remove a keyword mapping
    """
    user_profiles_col.update_one(
        {"auth0_user_id": auth0_user_id},
        {
            "$unset": {f"keywords.{keyword}": ""},
            "$set": {"last_updated": datetime.now().isoformat()}
        }
    )
    
    print(f"[User Profile] Removed keyword '{keyword}' for user: {auth0_user_id}")

def migrate_existing_users_add_keywords():
    """
    Migration function to add keywords field to existing users who don't have it
    """
    try:
        # Find all users without keywords field
        users_without_keywords = user_profiles_col.find({
            "auth0_user_id": {"$exists": True},
            "keywords": {"$exists": False}
        })
        
        count = 0
        for user in users_without_keywords:
            user_profiles_col.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "keywords": {},
                        "last_updated": datetime.now().isoformat()
                    }
                }
            )
            count += 1
            print(f"[Migration] Added keywords field to user: {user.get('auth0_user_id', 'unknown')}")
        
        print(f"[Migration] Successfully migrated {count} users to include keywords field")
        return count
        
    except Exception as e:
        print(f"[Migration] Error during keywords migration: {str(e)}")
        return 0
