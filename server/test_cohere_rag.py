"""
Test script for Cohere RAG location parsing
Run this to test the new RAG functionality with sample data
"""
import asyncio
import json
from services.cohere_rag_location_parser import CohereRAGLocationParser, parse_user_text_with_rag
from services.user_profile_service import add_keyword_location, get_user_keywords

async def test_rag_functionality():
    """
    Test the Cohere RAG location parsing with sample data
    """
    print("🧪 Testing Cohere RAG Location Parser")
    print("=" * 50)
    
    # Test user ID
    test_user_id = "test_rag_user_123"
    
    # Sample keywords to add to user profile
    sample_keywords = {
        "coffee": {
            "name": "Blue Bottle Coffee",
            "address": "123 Main St, San Francisco, CA",
            "lat": 37.7749,
            "lng": -122.4194,
            "place_id": "test_blue_bottle"
        },
        "museum": {
            "name": "SF Museum of Modern Art",
            "address": "151 3rd St, San Francisco, CA", 
            "lat": 37.7857,
            "lng": -122.4011,
            "place_id": "test_sfmoma"
        },
        "park": {
            "name": "Golden Gate Park",
            "address": "Golden Gate Park, San Francisco, CA",
            "lat": 37.7694,
            "lng": -122.4862,
            "place_id": "test_gg_park"
        },
        "restaurant": {
            "name": "Chez Panisse",
            "address": "1517 Shattuck Ave, Berkeley, CA",
            "lat": 37.8774,
            "lng": -122.2695,
            "place_id": "test_chez_panisse"
        }
    }
    
    print(f"📝 Adding sample keywords for user: {test_user_id}")
    
    # Add sample keywords to user profile
    for keyword, location_data in sample_keywords.items():
        try:
            add_keyword_location(test_user_id, keyword, location_data)
            print(f"  ✅ Added keyword: '{keyword}' -> {location_data['name']}")
        except Exception as e:
            print(f"  ❌ Failed to add keyword '{keyword}': {str(e)}")
    
    print("\n🔍 Testing RAG parsing with various user inputs...")
    
    # Test cases
    test_cases = [
        {
            "text": "I want to go to the coffee shop",
            "expected_keywords": ["coffee"],
            "description": "Direct keyword match"
        },
        {
            "text": "Let's visit the museum today",
            "expected_keywords": ["museum"],
            "description": "Museum reference"
        },
        {
            "text": "Can we go to the park for a walk?",
            "expected_keywords": ["park"],
            "description": "Park reference"
        },
        {
            "text": "I need to find a good restaurant",
            "expected_keywords": ["restaurant"],
            "description": "Restaurant reference"
        },
        {
            "text": "Show me places near Golden Gate",
            "expected_keywords": ["park"],
            "description": "Location-based reference"
        },
        {
            "text": "I want to grab some coffee and then visit an art museum",
            "expected_keywords": ["coffee", "museum"],
            "description": "Multiple keywords in one sentence"
        },
        {
            "text": "I need to find a grocery store",
            "expected_keywords": [],
            "description": "No matching keywords (should return empty)"
        }
    ]
    
    parser = CohereRAGLocationParser()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"   Input: '{test_case['text']}'")
        print(f"   Expected: {test_case['expected_keywords']}")
        
        try:
            result = parser.parse_user_text_for_keywords(
                user_text=test_case['text'],
                auth0_user_id=test_user_id
            )
            
            matched_keywords = result.get('matched_keywords', [])
            confidence_scores = result.get('confidence_scores', [])
            reasoning = result.get('parsed_intent', {}).get('reasoning', 'No reasoning provided')
            
            print(f"   ✅ RAG Results:")
            print(f"      Matched Keywords: {matched_keywords}")
            print(f"      Confidence Scores: {confidence_scores}")
            print(f"      Reasoning: {reasoning}")
            
            # Check if results match expectations
            if set(matched_keywords) == set(test_case['expected_keywords']):
                print(f"   🎯 PERFECT MATCH!")
            elif any(keyword in matched_keywords for keyword in test_case['expected_keywords']):
                print(f"   ✅ PARTIAL MATCH")
            else:
                print(f"   ⚠️  NO MATCH (expected: {test_case['expected_keywords']})")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n📊 Testing user keyword statistics...")
    try:
        stats = parser.get_user_keyword_stats(test_user_id)
        print(f"   Total Keywords: {stats['total_keywords']}")
        print(f"   Keyword List: {stats['keyword_list']}")
        print(f"   Location Types: {stats['location_types']}")
        print(f"   Recent Additions: {len(stats['recent_additions'])}")
    except Exception as e:
        print(f"   ❌ Error getting stats: {str(e)}")
    
    print("\n🔄 Testing comparison with current Gemini approach...")
    try:
        from services.llm_service import parse_intent
        
        test_text = "I want to go to the coffee shop"
        
        # RAG result
        rag_result = parse_user_text_with_rag(test_text, test_user_id)
        
        # Gemini result
        gemini_result = parse_intent("Current Location", test_text)
        
        print(f"   Test Input: '{test_text}'")
        print(f"   RAG Keywords: {rag_result.get('matched_keywords', [])}")
        print(f"   Gemini Places: {gemini_result.get('place_types', [])}")
        print(f"   Methods Differ: {rag_result.get('matched_keywords', []) != gemini_result.get('place_types', [])}")
        
    except Exception as e:
        print(f"   ❌ Comparison error: {str(e)}")
    
    print("\n✅ RAG testing completed!")
    print("\n📚 Next Steps:")
    print("   1. Test the API endpoints at http://localhost:8000/docs")
    print("   2. Try the /experimental/test-keywords endpoint")
    print("   3. Compare results with your current Gemini approach")
    print("   4. Add more keywords to your user profile for better testing")

if __name__ == "__main__":
    asyncio.run(test_rag_functionality())
