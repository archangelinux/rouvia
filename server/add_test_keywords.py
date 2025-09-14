"""
Quick script to add test keywords to a user profile for testing
"""
import os
import sys
sys.path.append('.')

from services.user_profile_service import add_keyword_location

def add_test_keywords():
    """Add some test keywords for demonstration"""
    
    # You can change this to your actual Auth0 user ID
    test_user_id = "test_user_123"
    
    # Sample keywords for testing
    test_keywords = {
        "coffee": {
            "name": "Blue Bottle Coffee",
            "address": "123 Main St, San Francisco, CA",
            "lat": 37.7749,
            "lng": -122.4194,
            "place_id": "test_blue_bottle"
        },
        "work": {
            "name": "Tech Company Office",
            "address": "456 Market St, San Francisco, CA",
            "lat": 37.7849,
            "lng": -122.4094,
            "place_id": "test_work_office"
        },
        "gym": {
            "name": "Fitness First Gym",
            "address": "789 Mission St, San Francisco, CA",
            "lat": 37.7649,
            "lng": -122.3994,
            "place_id": "test_gym"
        },
        "home": {
            "name": "My Apartment",
            "address": "100 Residential Ave, San Francisco, CA",
            "lat": 37.7849,
            "lng": -122.4094,
            "place_id": "test_home"
        }
    }
    
    print("Adding test keywords...")
    
    for keyword, location_data in test_keywords.items():
        try:
            add_keyword_location(test_user_id, keyword, location_data)
            print(f"✅ Added '{keyword}' -> {location_data['name']}")
        except Exception as e:
            print(f"❌ Failed to add '{keyword}': {str(e)}")
    
    print(f"\nTest user ID: {test_user_id}")
    print("You can now test with phrases like:")
    print("- 'I want to get coffee then go to work'")
    print("- 'Let me grab coffee before heading to the gym'")
    print("- 'Take me home after work'")

if __name__ == "__main__":
    add_test_keywords()
