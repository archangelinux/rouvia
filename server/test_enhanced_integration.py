"""
Test script for enhanced LLM service with RAG integration
Demonstrates the hybrid approach: Gemini identifies ambiguous words, RAG checks user keywords
"""
import asyncio
import json
from services.enhanced_llm_service import parse_intent_with_rag, select_stops
from services.user_profile_service import add_keyword_location, get_user_keywords

async def test_enhanced_integration():
    """
    Test the enhanced LLM service with RAG integration
    """
    print("🚀 Testing Enhanced LLM Service with RAG Integration")
    print("=" * 60)
    
    # Test user ID
    test_user_id = "test_enhanced_user_456"
    
    # Sample keywords for testing
    sample_keywords = {
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
        }
    }
    
    print(f"📝 Setting up test user: {test_user_id}")
    
    # Add sample keywords
    for keyword, location_data in sample_keywords.items():
        try:
            add_keyword_location(test_user_id, keyword, location_data)
            print(f"  ✅ Added keyword: '{keyword}' -> {location_data['name']}")
        except Exception as e:
            print(f"  ❌ Failed to add keyword '{keyword}': {str(e)}")
    
    print("\n🧪 Testing Enhanced Intent Parsing...")
    
    # Test cases that should trigger RAG keyword matching
    test_cases = [
        {
            "text": "I want to get coffee then go to work",
            "expected_keywords": ["coffee", "work"],
            "description": "Multiple personal locations"
        },
        {
            "text": "Let me grab coffee before heading to the gym",
            "expected_keywords": ["coffee", "gym"],
            "description": "Coffee and gym references"
        },
        {
            "text": "I need to go to work and then find a restaurant",
            "expected_keywords": ["work"],
            "description": "Personal location + general search"
        },
        {
            "text": "Can you help me find a museum and a coffee shop?",
            "expected_keywords": ["coffee"],
            "description": "General search with one personal match"
        },
        {
            "text": "I want to visit a park and go shopping",
            "expected_keywords": [],
            "description": "No personal location matches"
        },
        {
            "text": "Take me to my usual coffee spot",
            "expected_keywords": ["coffee"],
            "description": "Implicit personal reference"
        }
    ]
    
    # User location (San Francisco area)
    user_location = {"lat": 37.7749, "lng": -122.4194}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"   Input: '{test_case['text']}'")
        print(f"   Expected Keywords: {test_case['expected_keywords']}")
        
        try:
            result = parse_intent_with_rag(
                starting_location="San Francisco, CA",
                text=test_case['text'],
                auth0_user_id=test_user_id,
                user_location=user_location
            )
            
            # Extract key information
            rag_matches = result.get('rag_matches', [])
            unmatched_words = result.get('unmatched_ambiguous_words', [])
            personal_locations = result.get('personal_locations', [])
            unmatched_suggestions = result.get('unmatched_suggestions', [])
            
            print(f"   🔍 Analysis Results:")
            print(f"      RAG Matches: {len(rag_matches)}")
            for match in rag_matches:
                print(f"        - '{match['keyword']}' -> {match['location_data']['name']} ({match['distance_km']}km)")
            
            print(f"      Unmatched Words: {unmatched_words}")
            print(f"      Personal Locations: {len(personal_locations)}")
            print(f"      Suggestions: {len(unmatched_suggestions)}")
            
            if unmatched_suggestions:
                for suggestion in unmatched_suggestions:
                    print(f"        - '{suggestion['word']}': {suggestion['suggestion']}")
            
            # Check if results match expectations
            matched_keywords = [match['keyword'] for match in rag_matches]
            if set(matched_keywords) == set(test_case['expected_keywords']):
                print(f"   🎯 PERFECT MATCH!")
            elif any(keyword in matched_keywords for keyword in test_case['expected_keywords']):
                print(f"   ✅ PARTIAL MATCH")
            else:
                print(f"   ⚠️  NO MATCH (expected: {test_case['expected_keywords']})")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n🔄 Testing Distance Filtering...")
    
    # Test with a location far from user's keywords
    far_location = {"lat": 40.7128, "lng": -74.0060}  # New York
    
    print(f"   Testing with far location (NYC): {far_location}")
    
    try:
        result = parse_intent_with_rag(
            starting_location="New York, NY",
            text="I want to get coffee then go to work",
            auth0_user_id=test_user_id,
            user_location=far_location
        )
        
        rag_matches = result.get('rag_matches', [])
        print(f"   RAG Matches (should be empty due to distance): {len(rag_matches)}")
        
        if len(rag_matches) == 0:
            print(f"   ✅ Distance filtering working correctly")
        else:
            print(f"   ⚠️  Distance filtering may not be working")
            
    except Exception as e:
        print(f"   ❌ Distance test error: {str(e)}")
    
    print("\n📊 Testing Enhanced Stop Selection...")
    
    try:
        # Create a test intent with personal locations
        test_intent = {
            "place_types": [
                {
                    "name": "Blue Bottle Coffee",
                    "address": "123 Main St, San Francisco, CA",
                    "lat": 37.7749,
                    "lng": -122.4194,
                    "place_id": "test_blue_bottle",
                    "keyword": "coffee",
                    "distance_km": 0.1,
                    "confidence": 0.9,
                    "source": "user_keyword"
                },
                "museum"  # This would need Google Places search
            ],
            "personal_locations": [
                {
                    "name": "Blue Bottle Coffee",
                    "address": "123 Main St, San Francisco, CA",
                    "lat": 37.7749,
                    "lng": -122.4194,
                    "place_id": "test_blue_bottle",
                    "keyword": "coffee",
                    "distance_km": 0.1,
                    "confidence": 0.9,
                    "source": "user_keyword"
                }
            ],
            "has_personal_locations": True
        }
        
        # Mock candidates for Google Places
        mock_candidates = [
            {
                "name": "SF Museum of Modern Art",
                "address": "151 3rd St, San Francisco, CA",
                "lat": 37.7857,
                "lng": -122.4011,
                "place_id": "mock_museum"
            }
        ]
        
        selected_stops = select_stops(test_intent, mock_candidates)
        
        print(f"   Selected Stops: {len(selected_stops)}")
        for stop in selected_stops:
            source = stop.get('source', 'google_places')
            print(f"     - {stop.get('name', 'Unknown')} (source: {source})")
        
        # Check if personal locations are prioritized
        personal_stops = [stop for stop in selected_stops if stop.get('source') == 'user_keyword']
        if personal_stops:
            print(f"   ✅ Personal locations prioritized: {len(personal_stops)}")
        else:
            print(f"   ⚠️  Personal locations not found in selection")
            
    except Exception as e:
        print(f"   ❌ Stop selection error: {str(e)}")
    
    print("\n✅ Enhanced integration testing completed!")
    print("\n📚 Next Steps:")
    print("   1. Test the enhanced API endpoints:")
    print("      - POST /enhanced-plan-route-text")
    print("      - POST /enhanced-plan-route-audio")
    print("      - POST /compare-enhanced-vs-standard")
    print("   2. Add more keywords to your user profile")
    print("   3. Test with real user scenarios")
    print("   4. Monitor the 20km radius filtering")

if __name__ == "__main__":
    asyncio.run(test_enhanced_integration())
