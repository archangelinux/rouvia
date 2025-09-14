#!/usr/bin/env python3
"""
Test script to write data via API endpoints
"""
import requests
import json
import time

def test_api_write():
    """Test writing data via API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test data
    test_locations = [
        {
            "name": "home",
            "coords": [0, 0],
            "address": "423 Mayorview Dr, Burlington, ON L4E 9W2"
        },
        {
            "name": "work", 
            "coords": [0, 0],
            "address": "1003 Bloor St, Toronto, ON N2J 2J9"
        }
    ]
    
    print("🔄 Testing API endpoints...")
    
    # Test server health
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Test writing locations
    for location in test_locations:
        try:
            print(f"📝 Writing {location['name']} location...")
            response = requests.post(
                f"{base_url}/update-location/test_user",
                json=location,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {location['name']} written successfully: {result}")
            else:
                print(f"❌ Failed to write {location['name']}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error writing {location['name']}: {e}")
    
    # Test reading locations
    try:
        print("📖 Reading saved locations...")
        response = requests.get(f"{base_url}/saved-locations/test_user", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved locations: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Failed to read locations: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error reading locations: {e}")
    
    return True

if __name__ == "__main__":
    test_api_write()
