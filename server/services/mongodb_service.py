from pymongo import MongoClient
from typing import Optional, Dict, Any
import os
from datetime import datetime

class MongoDBService:
    def __init__(self):
        mongodb_url = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = MongoClient(mongodb_url)
        self.db = self.client.sidequest_db
        self.user_profiles = self.db.user_profiles

    def get_user_profile(self, auth0_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by Auth0 user ID
        """
        try:
            profile = self.user_profiles.find_one({"auth0_user_id": auth0_user_id})
            return profile
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            return None

    def get_user_profile_by_auth0_id(self, auth0_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by Auth0 user ID (alias for get_user_profile for clarity)
        """
        return self.get_user_profile(auth0_user_id)

    def get_user_preferences(self, auth0_user_id: str) -> Dict[str, Any]:
        """
        Get user preferences section from profile
        """
        profile = self.get_user_profile(auth0_user_id)
        if profile:
            return profile.get("preferences", {})
        return {}

    def get_user_keywords(self, auth0_user_id: str) -> Dict[str, Any]:
        """
        Get user keywords section from profile
        """
        profile = self.get_user_profile(auth0_user_id)
        if profile:
            return profile.get("keywords", {})
        return {}

    def update_user_visited_places(self, auth0_user_id: str, place_info: Dict[str, Any]) -> bool:
        """
        Add a place to user's visited places
        """
        try:
            result = self.user_profiles.update_one(
                {"auth0_user_id": auth0_user_id},
                {
                    "$push": {"visited_places": place_info},
                    "$set": {"last_updated": datetime.utcnow().isoformat()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating visited places: {e}")
            return False

# Global instance
mongodb_service = MongoDBService()
