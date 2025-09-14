#!/usr/bin/env python3
"""
Simple script to write test data to MongoDB with SSL bypass
"""
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import ssl

# Load environment variables
load_dotenv()

def write_test_data():
    try:
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI not found in environment variables")
            return False
        
        print(f"🔌 Connecting to MongoDB with URI: {mongo_uri[:50]}...")
        
        # Try different connection methods
        try:
            # Method 1: Default connection
            client = MongoClient(mongo_uri)
            client.admin.command('ping')
            print("✅ Connected with default settings")
        except Exception as e1:
            print(f"❌ Default connection failed: {e1}")
            try:
                # Method 2: SSL disabled
                client = MongoClient(mongo_uri, ssl=False, ssl_cert_reqs=ssl.CERT_NONE)
                client.admin.command('ping')
                print("✅ Connected with SSL disabled")
            except Exception as e2:
                print(f"❌ SSL disabled connection failed: {e2}")
                try:
                    # Method 3: TLS with invalid certs allowed
                    client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
                    client.admin.command('ping')
                    print("✅ Connected with TLS invalid certs allowed")
                except Exception as e3:
                    print(f"❌ All connection methods failed:")
                    print(f"   Default: {e1}")
                    print(f"   SSL disabled: {e2}")
                    print(f"   TLS invalid certs: {e3}")
                    return False
        
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
    success = write_test_data()
    sys.exit(0 if success else 1)
