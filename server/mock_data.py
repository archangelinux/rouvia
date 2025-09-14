#!/usr/bin/env python3
"""
Mock data storage for testing when MongoDB is not available
"""
import json
import os
from datetime import datetime

# Mock data file
MOCK_DATA_FILE = "mock_user_data.json"

def load_mock_data():
    """Load mock data from file"""
    if os.path.exists(MOCK_DATA_FILE):
        with open(MOCK_DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        # Return default test data
        return {
            "test_user": {
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
        }

def save_mock_data(data):
    """Save mock data to file"""
    with open(MOCK_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_user_location(user_id, location_name, location_data):
    """Update user location in mock data"""
    data = load_mock_data()
    
    if user_id not in data:
        data[user_id] = {
            "user_id": user_id,
            "locations": {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    data[user_id]["locations"][location_name] = location_data
    data[user_id]["last_updated"] = datetime.now().isoformat()
    
    save_mock_data(data)
    return True

def get_user_locations(user_id):
    """Get user locations from mock data"""
    data = load_mock_data()
    user_data = data.get(user_id, {})
    return user_data.get("locations", {})

# Initialize mock data
if __name__ == "__main__":
    data = load_mock_data()
    print("📝 Mock data initialized:")
    print(json.dumps(data, indent=2))
