#!/usr/bin/env python3
"""
Test script to verify MongoDB Atlas connection with SSL fixes
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import ssl

# Load environment variables
load_dotenv()

def test_mongo_connection_ssl():
    """Test MongoDB Atlas connection with SSL fixes"""
    MONGO_URI = os.getenv("MONGO_URI")
    
    print(f"MONGO_URI: {MONGO_URI}")
    
    if not MONGO_URI or "username:password" in MONGO_URI:
        print("❌ ERROR: MONGO_URI is not set or still has placeholder values!")
        return False
    
    try:
        # Test connection with SSL context
        client = MongoClient(
            MONGO_URI,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,  # Disable SSL certificate verification
            ssl_ca_certs=None,
            retryWrites=True
        )
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database and collections
        db = client["sidequest_db"]
        collections = db.list_collection_names()
        print(f"📊 Collections in sidequest_db: {collections}")
        
        # Test user_profiles collection
        user_profiles_col = db["user_profiles"]
        
        # Count existing documents
        count = user_profiles_col.count_documents({})
        print(f"👤 User profiles count: {count}")
        
        # Show existing profiles
        if count > 0:
            print("📋 Existing user profiles:")
            for profile in user_profiles_col.find({}):
                print(f"  - User ID: {profile.get('user_id', 'Unknown')}")
                print(f"    Saved locations: {len(profile.get('saved_locations', []))}")
                print(f"    Visited places: {len(profile.get('visited_places', []))}")
        
        # Test creating a test profile
        test_profile = {
            "user_id": "test_connection_user",
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
        
        # Insert test profile
        result = user_profiles_col.insert_one(test_profile)
        print(f"✅ Test profile inserted with ID: {result.inserted_id}")
        
        # Verify it was inserted
        test_count = user_profiles_col.count_documents({"user_id": "test_connection_user"})
        print(f"✅ Test profile count: {test_count}")
        
        # Clean up test profile
        user_profiles_col.delete_one({"user_id": "test_connection_user"})
        print("🧹 Test profile cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ ERROR connecting to MongoDB: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing MongoDB Atlas connection with SSL fixes...")
    success = test_mongo_connection_ssl()
    
    if success:
        print("\n🎉 MongoDB connection test PASSED!")
    else:
        print("\n💥 MongoDB connection test FAILED!")
        print("\nAlternative solutions:")
        print("1. Check your IP is whitelisted in MongoDB Atlas")
        print("2. Try updating your connection string to include ssl=true")
        print("3. Check if your MongoDB user has proper permissions")
