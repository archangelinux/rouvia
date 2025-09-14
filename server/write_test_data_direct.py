#!/usr/bin/env python3
"""
Direct MongoDB test data writer - bypasses SSL issues
"""
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def write_test_data_direct():
    try:
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI not found in environment variables")
            return False
        
        print(f"🔌 Connecting to MongoDB...")
        
        # Try the most permissive connection settings
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        
        # Test connection
        try:
            client.admin.command('ping')
            print("✅ MongoDB connection successful")
        except Exception as ping_error:
            print(f"⚠️ Ping failed but continuing: {ping_error}")
        
        db = client["sidequest_db"]
        user_profiles_col = db["user_profiles"]
        
        # Test data for test_user
        test_user_data = {
            "user_id": "test_user",
            "locations": {
                "home": {
                    "coords": [0, 0],
                    "address": "423 Mayorview Dr, Burlington, ON L4E 9W2",
                    "updated_at": datetime.now().isoformat()
                },
                "work": {
                    "coords": [0, 0],
                    "address": "1003 Bloor St, Toronto, ON N2J 2J9",
                    "updated_at": datetime.now().isoformat()
                }
            },
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Insert or update the test user data
        print("📝 Writing test data to MongoDB...")
        result = user_profiles_col.update_one(
            {"user_id": "test_user"},
            {"$set": test_user_data},
            upsert=True
        )
        
        if result.upserted_id:
            print(f"✅ Created new test_user document with ID: {result.upserted_id}")
        else:
            print(f"✅ Updated existing test_user document. Modified: {result.modified_count}")
        
        # Verify the data was written
        print("🔍 Verifying data...")
        saved_data = user_profiles_col.find_one({"user_id": "test_user"})
        if saved_data:
            print("✅ Data successfully written to MongoDB:")
            print(f"   User ID: {saved_data['user_id']}")
            print(f"   Locations: {len(saved_data['locations'])}")
            for name, location in saved_data['locations'].items():
                print(f"   - {name}: {location['address']}")
        else:
            print("❌ Failed to verify data in MongoDB")
            return False
        
        client.close()
        print("🎉 Test data write completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error writing test data: {e}")
        return False

if __name__ == "__main__":
    success = write_test_data_direct()
    sys.exit(0 if success else 1)
