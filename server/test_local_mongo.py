#!/usr/bin/env python3
"""
Test with local MongoDB fallback
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def test_local_fallback():
    """Test with local MongoDB if Atlas fails"""
    try:
        # Try local MongoDB first
        print("Testing local MongoDB...")
        local_client = MongoClient("mongodb://localhost:27017/")
        local_client.admin.command('ping')
        print("✅ Local MongoDB connection successful!")
        
        # Use local database
        db = local_client["sidequest_db"]
        user_profiles_col = db["user_profiles"]
        
        # Test operations
        count = user_profiles_col.count_documents({})
        print(f"Local DB has {count} user profiles")
        
        # Create test profile
        test_profile = {
            "user_id": "test_local_user",
            "saved_locations": [
                {
                    "id": "1",
                    "name": "Test Home",
                    "address": "123 Test St, Test City, ON"
                }
            ],
            "visited_places": [],
            "preferences": {
                "favorite_cuisines": ["test"],
                "budget_range": "test",
                "energy_level": 5
            },
            "created_at": "2024-01-15T10:30:00Z",
            "last_updated": "2024-01-15T10:30:00Z"
        }
        
        result = user_profiles_col.insert_one(test_profile)
        print(f"✅ Test profile inserted with ID: {result.inserted_id}")
        
        # Clean up
        user_profiles_col.delete_one({"user_id": "test_local_user"})
        print("🧹 Test profile cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Local MongoDB failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing local MongoDB fallback...")
    test_local_fallback()
