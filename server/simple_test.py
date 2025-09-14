#!/usr/bin/env python3
"""
Simple test to check MongoDB connection
"""
from services.mongo import user_profiles_col

def test_simple_connection():
    try:
        # Test basic operations
        count = user_profiles_col.count_documents({})
        print(f"✅ Connection successful! Found {count} user profiles")
        
        # List all user profiles
        profiles = list(user_profiles_col.find({}))
        for profile in profiles:
            print(f"  - User: {profile.get('user_id', 'Unknown')}")
            print(f"    Saved locations: {len(profile.get('saved_locations', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing simple MongoDB connection...")
    test_simple_connection()
