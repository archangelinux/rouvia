"""
Test script for order preservation and keyword priority rules
"""
import asyncio
import json
from services.enhanced_llm_service import parse_intent_with_rag, select_stops
from services.user_profile_service import add_keyword_location, get_user_keywords

async def test_order_preservation():
    """
    Test the order preservation and keyword priority rules
    """
    print("🧪 Testing Order Preservation and Keyword Priority Rules")
    print("=" * 60)
    
    # Test user ID
    test_user_id = "test_order_user_789"
    
    # Sample keywords for testing
    sample_keywords = {
        "work": {
            "name": "Tech Company Office",
            "address": "456 Market St, San Francisco, CA",
            "lat": 37.7849,
            "lng": -122.4094,
            "place_id": "test_work_office"
        },
        "chicken": {
            "name": "Popeyes Chicken",
            "address": "789 Mission St, San Francisco, CA",
            "lat": 37.7649,
            "lng": -122.3994,
            "place_id": "test_popeyes"
        },
        "coffee": {
            "name": "Blue Bottle Coffee",
            "address": "123 Main St, San Francisco, CA",
            "lat": 37.7749,
            "lng": -122.4194,
            "place_id": "test_blue_bottle"
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
    
    print("\n🧪 Testing Order Preservation...")
    
    # Test cases for order preservation
    test_cases = [
        {
            "text": "I go to work then buy chicken",
            "expected_order": ["work", "chicken"],
            "description": "Sequential order: personal work first, then general chicken"
        },
        {
            "text": "I go to work but first I will get chicken",
            "expected_order": ["chicken", "work"],
            "description": "Reverse order: general chicken first, then personal work"
        },
        {
            "text": "Take me to my coffee shop",
            "expected_order": ["coffee"],
            "description": "Single personal location, no alternatives needed"
        },
        {
            "text": "I'm feeling like a different coffee place today",
            "expected_order": ["coffee"],
            "wants_alternatives": True,
            "description": "Single personal location but wants alternatives"
        },
        {
            "text": "I need to get coffee then go to work",
            "expected_order": ["coffee", "work"],
            "description": "Personal coffee first, then personal work"
        },
        {
            "text": "I want to buy chicken then go to work then get coffee",
            "expected_order": ["chicken", "work", "coffee"],
            "description": "Mixed order: general chicken, personal work, personal coffee"
        },
        {
            "text": "First I'll get coffee, then buy chicken, and finally go to work",
            "expected_order": ["coffee", "chicken", "work"],
            "description": "Explicit order: personal coffee, general chicken, personal work"
        }
    ]
    
    # User location (San Francisco area)
    user_location = {"lat": 37.7749, "lng": -122.4194}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"   Input: '{test_case['text']}'")
        print(f"   Expected Order: {test_case['expected_order']}")
        
        try:
            result = parse_intent_with_rag(
                starting_location="San Francisco, CA",
                text=test_case['text'],
                auth0_user_id=test_user_id,
                user_location=user_location
            )
            
            # Extract key information
            rag_matches = result.get('rag_matches', [])
            order_preserved = result.get('order_preserved', False)
            wants_alternatives = result.get('wants_alternatives', False)
            personal_locations = result.get('personal_locations', [])
            complete_order = result.get('complete_order', [])
            
            print(f"   🔍 Analysis Results:")
            print(f"      RAG Matches: {len(rag_matches)}")
            for match in rag_matches:
                print(f"        - '{match['keyword']}' -> {match['location_data']['name']} ({match['distance_km']}km)")
            
            print(f"      Order Preserved: {order_preserved}")
            print(f"      Wants Alternatives: {wants_alternatives}")
            print(f"      Personal Locations: {len(personal_locations)}")
            print(f"      Complete Order: {len(complete_order)}")
            
            # Check complete order
            if complete_order:
                sorted_order = sorted(complete_order, key=lambda x: x.get('order_index', 0))
                order_keywords = [loc['keyword'] for loc in sorted_order]
                print(f"        Complete order keywords: {order_keywords}")
                
                if order_keywords == test_case['expected_order']:
                    print(f"   🎯 PERFECT COMPLETE ORDER MATCH!")
                else:
                    print(f"   ⚠️  COMPLETE ORDER MISMATCH (expected: {test_case['expected_order']}, got: {order_keywords})")
            else:
                # Fallback: check RAG matches order
                matched_keywords = [match['keyword'] for match in rag_matches]
                if matched_keywords == test_case['expected_order']:
                    print(f"   🎯 PERFECT RAG ORDER MATCH!")
                else:
                    print(f"   ⚠️  RAG ORDER MISMATCH (expected: {test_case['expected_order']}, got: {matched_keywords})")
            
            # Check alternatives flag
            if test_case.get('wants_alternatives', False) == wants_alternatives:
                print(f"   ✅ Alternatives flag correct: {wants_alternatives}")
            else:
                print(f"   ⚠️  Alternatives flag mismatch (expected: {test_case.get('wants_alternatives', False)}, got: {wants_alternatives})")
            
            # Test stop selection
            print(f"   🛑 Testing Stop Selection...")
            selected_stops = select_stops(result, [])
            stop_keywords = [stop.get('keyword', 'unknown') for stop in selected_stops]
            print(f"      Selected Stops: {stop_keywords}")
            
            if stop_keywords == test_case['expected_order']:
                print(f"   🎯 STOP SELECTION ORDER PERFECT!")
            else:
                print(f"   ⚠️  STOP SELECTION ORDER MISMATCH")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n✅ Order preservation testing completed!")
    print("\n📚 Key Rules Implemented:")
    print("   1. ORDER PRESERVATION: Locations mentioned in sequence are visited in that order")
    print("   2. KEYWORD PRIORITY: Personal keywords take precedence over general search")
    print("   3. ALTERNATIVES: Only search for alternatives when explicitly requested")
    print("   4. DISTANCE FILTERING: Personal locations must be within 20km")

if __name__ == "__main__":
    asyncio.run(test_order_preservation())
