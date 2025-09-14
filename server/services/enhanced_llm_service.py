"""
Enhanced LLM service that integrates Cohere RAG for user keyword checking
This extends the existing Gemini-based parsing with RAG keyword analysis
"""
from google import genai
import os
import json
import math
from typing import Dict, List, Any, Optional, Tuple
from services.cohere_rag_location_parser import CohereRAGLocationParser

def _get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def parse_intent_with_rag(
    starting_location: str, 
    text: str, 
    auth0_user_id: Optional[str] = None,
    user_location: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Enhanced intent parsing that first checks for user keywords using RAG,
    then falls back to standard Gemini parsing for unmatched terms.
    
    Args:
        starting_location: The user's starting location as a string
        text: Transcribed text from user audio input
        auth0_user_id: User's Auth0 ID for keyword checking
        user_location: User's current location {"lat": x, "lng": y}
        
    Returns:
        Enhanced intent dictionary with RAG keyword matches
    """
    
    # Step 1: Use Gemini to identify potentially ambiguous words
    ambiguous_words = _identify_ambiguous_words(text)
    print(f"[Enhanced LLM] Identified ambiguous words: {ambiguous_words}")
    
    # Step 2: Check user keywords for ALL ambiguous words first
    rag_matches = []
    unmatched_words = []
    wants_alternatives = False
    order_preserved = True
    
    if auth0_user_id and ambiguous_words:
        rag_parser = CohereRAGLocationParser()
        rag_result = rag_parser.parse_user_text_for_keywords(
            user_text=text,
            auth0_user_id=auth0_user_id,
            context_location=user_location
        )
        
        matched_keywords = rag_result.get('matched_keywords', [])
        location_data = rag_result.get('location_data', [])
        wants_alternatives = rag_result.get('wants_alternatives', False)
        order_preserved = rag_result.get('order_preserved', True)
        
        # Filter matches by distance (20km radius) and confidence
        if user_location and location_data:
            filtered_matches = []
            for match in location_data:
                location_info = match.get('location_data', {})
                match_lat = location_info.get('lat')
                match_lng = location_info.get('lng')
                confidence = match.get('confidence', 0.5)
                
                if match_lat and match_lng:
                    distance = calculate_distance(
                        user_location['lat'], user_location['lng'],
                        match_lat, match_lng
                    )
                    
                    # Only use personal location if it's close AND confident
                    if distance <= 20 and confidence >= 0.7:  # 20km radius + high confidence
                        filtered_matches.append({
                            'keyword': match.get('keyword'),
                            'location_data': location_info,
                            'distance_km': round(distance, 2),
                            'confidence': confidence
                        })
                        print(f"[Enhanced LLM] RAG match accepted: {match.get('keyword')} ({distance:.2f}km, confidence: {confidence:.2f})")
                    else:
                        print(f"[Enhanced LLM] RAG match rejected: {match.get('keyword')} (distance: {distance:.2f}km, confidence: {confidence:.2f})")
            
            rag_matches = filtered_matches
        
        # KEYWORD PRIORITY RULE: If personal keywords are matched and user doesn't want alternatives,
        # don't search for additional locations unless explicitly needed
        if rag_matches and not wants_alternatives:
            print(f"[Enhanced LLM] Personal keywords found, skipping Google Places search for: {[match['keyword'] for match in rag_matches]}")
            unmatched_words = []  # Don't search for alternatives
        else:
            # Identify unmatched ambiguous words (these will use Google Places)
            matched_keyword_names = [match['keyword'] for match in rag_matches]
            unmatched_words = [word for word in ambiguous_words if word not in matched_keyword_names]
            print(f"[Enhanced LLM] Unmatched words (will use Google Places): {unmatched_words}")
    
    # Step 3: Parse complete order of ALL locations (personal + general)
    complete_order = _parse_complete_location_order(text, rag_matches, ambiguous_words)
    
    # Step 4: Use standard Gemini parsing for unmatched words
    standard_intent = _parse_intent_standard(starting_location, text)
    
    # Step 5: Enhance the intent with RAG matches and complete order
    enhanced_intent = _enhance_intent_with_rag(
        standard_intent, 
        rag_matches, 
        unmatched_words,
        text,
        order_preserved,
        wants_alternatives,
        complete_order
    )
    
    return enhanced_intent

def _parse_complete_location_order(text: str, rag_matches: List[Dict[str, Any]], ambiguous_words: List[str]) -> List[Dict[str, Any]]:
    """
    Parse the complete order of ALL locations mentioned (personal + general) using Gemini
    """
    try:
        # Create a list of all mentioned locations
        all_locations = []
        
        # Add personal locations from RAG matches
        for match in rag_matches:
            all_locations.append({
                "type": "personal",
                "keyword": match['keyword'],
                "name": match['location_data']['name'],
                "source": "user_keyword"
            })
        
        # Add general locations from ambiguous words
        for word in ambiguous_words:
            all_locations.append({
                "type": "general", 
                "keyword": word,
                "name": word,
                "source": "google_places"
            })
        
        if not all_locations:
            return []
        
        # Use Gemini to determine the order
        system_rules = """
        You are a location order parser. Your job is to analyze user text and determine the ORDER in which locations should be visited.
        
        Return a JSON array of location objects in the order they should be visited, with:
        - "keyword": the keyword/term mentioned
        - "type": "personal" or "general" 
        - "order_index": the position in the sequence (0-based)
        - "reasoning": why this location comes at this position
        
        Look for order indicators:
        - "then", "after", "next" = sequential order
        - "first", "before" = priority order
        - "and" = simultaneous or sequential depending on context
        
        Examples:
        - "I go to work then buy chicken" → [{"keyword": "work", "type": "personal", "order_index": 0}, {"keyword": "chicken", "type": "general", "order_index": 1}]
        - "I go to work but first I will get chicken" → [{"keyword": "chicken", "type": "general", "order_index": 0}, {"keyword": "work", "type": "personal", "order_index": 1}]
        """
        
        locations_str = json.dumps(all_locations)
        prompt = f"{system_rules}\nUser text: {text}\nAll mentioned locations: {locations_str}"
        
        client = _get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        
        result = json.loads(response.text)
        print(f"[Complete Order] Parsed order: {result}")
        return result
        
    except Exception as e:
        print(f"[Complete Order] Error parsing order: {str(e)}")
        # Fallback: return locations in the order they appear in text
        fallback_order = []
        for i, location in enumerate(all_locations):
            fallback_order.append({
                "keyword": location["keyword"],
                "type": location["type"],
                "order_index": i,
                "reasoning": "fallback_order"
            })
        return fallback_order

def _identify_ambiguous_words(text: str) -> List[str]:
    """
    Use Gemini to identify potentially ambiguous words that could be personal locations
    """
    system_rules = """
    You are a location ambiguity detector. Your job is to identify words in user text that could potentially refer to personal locations or places the user has saved.

    Return a JSON object with:
    - "ambiguous_words": Array of words/phrases that could be personal locations
    - "reasoning": Brief explanation of why these words were identified as ambiguous

    Examples of ambiguous words:
    - "coffee" (could be a specific coffee shop they frequent)
    - "work" (could be their workplace)
    - "gym" (could be their specific gym)
    - "home" (could be their home address)
    - "mom's house" (could be a saved location)
    - "the usual spot" (could be a saved location)

    Only identify words that are genuinely ambiguous and could refer to personal locations.
    Don't include obvious general categories like "restaurant" or "museum" unless context suggests personal reference.
    """
    
    prompt = f"{system_rules}\nUser text: {text}"
    
    try:
        client = _get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        
        result = json.loads(response.text)
        ambiguous_words = result.get("ambiguous_words", [])
        print(f"[Enhanced LLM] Ambiguous words identified: {ambiguous_words}")
        return ambiguous_words
        
    except Exception as e:
        print(f"[Enhanced LLM] Error identifying ambiguous words: {str(e)}")
        return []

def _parse_intent_standard(starting_location: str, text: str) -> Dict[str, Any]:
    """
    Standard Gemini intent parsing (existing functionality)
    """
    system_rules = (
        "You will first check if the user specifies specific locations. If so, prioritize those locations over general categories. "
        "If specific locations are provided, return them directly. If only categories are given, proceed to select places based on those categories. "
        "Return a STRICT JSON object with exactly three keys: "
        "1) 'place_types': an array where each element can be either a single search term OR an array of related search terms that add context for finding the same destination. These can be specific place names (e.g., 'Starbucks', 'CN Tower'), general categories (e.g., 'coffee shop', 'museum'), or descriptive terms (e.g., 'scenic viewpoint', 'late night food'). When using arrays, all terms should describe the same place to provide better search context. For example: ['coffee shop'] or [['italian restaurant', 'pasta', 'romantic atmosphere', 'downtown new york']] or ['CN Tower']. The array terms will be combined to find one location that matches all the context. "
        "2) 'last_destination': a string representing the last destination the user wants to visit. This should be the final destination in 'place_types'. "
        "3) 'search_radius_meters': an integer representing the search radius in meters from the starting location. Default to 10000 meters for general searches, but increase to whatever amount for specific named locations that might be farther away. "
        "If the user specifies only one destination, 'last_destination' should match that destination, and 'place_types' should contain only that destination. "
        "Use arrays of terms when the user provides rich context about what they want (atmosphere, location, food type, occasion, etc.) to help find the perfect match. "
        "No extra text. No markdown. No code fences."
    )

    prompt = f"{system_rules}\n Starting location: {starting_location}\n User text: {text}"

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    print(f"Gemini raw response: {response.text}")

    # Parse the JSON string response into a Python dict
    intent_data = json.loads(response.text)
    return intent_data

def _enhance_intent_with_rag(
    standard_intent: Dict[str, Any],
    rag_matches: List[Dict[str, Any]],
    unmatched_words: List[str],
    original_text: str,
    order_preserved: bool = True,
    wants_alternatives: bool = False,
    complete_order: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enhance the standard intent with RAG keyword matches and handle unmatched words
    """
    enhanced_intent = standard_intent.copy()
    
    # Add RAG-specific fields
    enhanced_intent["rag_matches"] = rag_matches
    enhanced_intent["unmatched_ambiguous_words"] = unmatched_words
    enhanced_intent["has_personal_locations"] = len(rag_matches) > 0
    enhanced_intent["order_preserved"] = order_preserved
    enhanced_intent["wants_alternatives"] = wants_alternatives
    enhanced_intent["complete_order"] = complete_order or []
    
    # COMPLETE ORDER PRESERVATION: Create ordered place_types from complete order
    if complete_order and order_preserved:
        ordered_place_types = []
        personal_locations = []
        
        # Sort complete order by order_index
        sorted_order = sorted(complete_order, key=lambda x: x.get('order_index', 0))
        
        for location_order in sorted_order:
            keyword = location_order['keyword']
            location_type = location_order['type']
            
            if location_type == "personal":
                # Find the personal location data
                personal_match = next((match for match in rag_matches if match['keyword'] == keyword), None)
                if personal_match:
                    location_data = personal_match['location_data']
                    location_obj = {
                        "name": location_data.get('name'),
                        "address": location_data.get('address'),
                        "lat": location_data.get('lat'),
                        "lng": location_data.get('lng'),
                        "place_id": location_data.get('place_id'),
                        "keyword": keyword,
                        "distance_km": personal_match['distance_km'],
                        "confidence": personal_match['confidence'],
                        "source": "user_keyword",
                        "order_index": location_order.get('order_index', 0)
                    }
                    ordered_place_types.append(location_obj)
                    personal_locations.append(location_obj)
            else:
                # General location - add as string for Google Places search
                ordered_place_types.append({
                    "keyword": keyword,
                    "type": "general",
                    "source": "google_places",
                    "order_index": location_order.get('order_index', 0)
                })
        
        enhanced_intent["place_types"] = ordered_place_types
        enhanced_intent["personal_locations"] = personal_locations
        print(f"[Enhanced LLM] Complete order preserved: {[loc.get('keyword', loc.get('name', 'unknown')) for loc in ordered_place_types]}")
    
    elif rag_matches:
        # Fallback: just add personal locations (old behavior)
        personal_locations = []
        for match in rag_matches:
            location_data = match['location_data']
            personal_locations.append({
                "name": location_data.get('name'),
                "address": location_data.get('address'),
                "lat": location_data.get('lat'),
                "lng": location_data.get('lng'),
                "place_id": location_data.get('place_id'),
                "keyword": match['keyword'],
                "distance_km": match['distance_km'],
                "confidence": match['confidence'],
                "source": "user_keyword"
            })
        
        # Append to existing place_types
        if "place_types" not in enhanced_intent:
            enhanced_intent["place_types"] = []
        enhanced_intent["place_types"].extend(personal_locations)
        enhanced_intent["personal_locations"] = personal_locations
    
    # Handle unmatched ambiguous words
    if unmatched_words:
        enhanced_intent["unmatched_suggestions"] = _generate_unmatched_suggestions(unmatched_words, original_text)
    
    return enhanced_intent

def _generate_unmatched_suggestions(unmatched_words: List[str], original_text: str) -> List[Dict[str, str]]:
    """
    Generate suggestions for unmatched ambiguous words
    """
    suggestions = []
    
    for word in unmatched_words:
        if word.lower() in ["work", "office", "job"]:
            suggestions.append({
                "word": word,
                "suggestion": "Please specify your workplace location or add it to your saved locations",
                "action": "add_location"
            })
        elif word.lower() in ["home", "house"]:
            suggestions.append({
                "word": word,
                "suggestion": "Please specify your home address or add it to your saved locations",
                "action": "add_location"
            })
        elif word.lower() in ["gym", "fitness"]:
            suggestions.append({
                "word": word,
                "suggestion": "Please specify your gym location or add it to your saved locations",
                "action": "add_location"
            })
        else:
            suggestions.append({
                "word": word,
                "suggestion": f"Please specify what '{word}' refers to or add it to your saved locations",
                "action": "add_location"
            })
    
    return suggestions

def select_stops(intent: dict, candidates: list) -> list:
    """
    Enhanced stop selection that preserves complete order of ALL locations (personal + general)
    """
    complete_order = intent.get("complete_order", [])
    order_preserved = intent.get("order_preserved", True)
    personal_locations = intent.get("personal_locations", [])
    
    if complete_order and order_preserved:
        # COMPLETE ORDER PRESERVATION: Handle both personal and general locations in order
        selected_stops = []
        
        # Sort by order_index
        sorted_order = sorted(complete_order, key=lambda x: x.get('order_index', 0))
        
        for location_order in sorted_order:
            keyword = location_order['keyword']
            location_type = location_order['type']
            
            if location_type == "personal":
                # Use personal location data
                personal_loc = next((loc for loc in personal_locations if loc['keyword'] == keyword), None)
                if personal_loc:
                    selected_stops.append({
                        "name": personal_loc["name"],
                        "address": personal_loc["address"],
                        "lat": personal_loc["lat"],
                        "lng": personal_loc["lng"],
                        "place_id": personal_loc["place_id"],
                        "types": ["personal_location"],
                        "rating": 5.0,
                        "user_ratings_total": 1,
                        "source": "user_keyword",
                        "keyword": keyword,
                        "distance_km": personal_loc["distance_km"],
                        "confidence": personal_loc["confidence"],
                        "order_index": location_order.get('order_index', 0)
                    })
            else:
                # Find matching candidate from Google Places
                matching_candidate = next((c for c in candidates if keyword.lower() in c.get('name', '').lower() or 
                                         any(keyword.lower() in t.lower() for t in c.get('types', []))), None)
                if matching_candidate:
                    selected_stops.append({
                        "name": matching_candidate.get('name'),
                        "address": matching_candidate.get('address'),
                        "lat": matching_candidate.get('lat'),
                        "lng": matching_candidate.get('lng'),
                        "place_id": matching_candidate.get('place_id'),
                        "types": matching_candidate.get('types', []),
                        "rating": matching_candidate.get('rating', 0),
                        "user_ratings_total": matching_candidate.get('user_ratings_total', 0),
                        "source": "google_places",
                        "keyword": keyword,
                        "order_index": location_order.get('order_index', 0)
                    })
        
        print(f"[Enhanced LLM] Complete order preserved: {[stop.get('keyword', stop.get('name', 'unknown')) for stop in selected_stops]}")
        return selected_stops
    
    elif personal_locations:
        # Fallback: Use personal locations only (old behavior)
        selected_stops = []
        
        for personal_loc in personal_locations:
            selected_stops.append({
                "name": personal_loc["name"],
                "address": personal_loc["address"],
                "lat": personal_loc["lat"],
                "lng": personal_loc["lng"],
                "place_id": personal_loc["place_id"],
                "types": ["personal_location"],
                "rating": 5.0,
                "user_ratings_total": 1,
                "source": "user_keyword",
                "keyword": personal_loc["keyword"],
                "distance_km": personal_loc["distance_km"],
                "confidence": personal_loc["confidence"]
            })
        
        # Add remaining stops from standard selection
        remaining_intent = intent.copy()
        remaining_intent["place_types"] = [pt for pt in intent.get("place_types", []) 
                                        if not isinstance(pt, dict) or pt.get("source") != "user_keyword"]
        
        if remaining_intent["place_types"]:
            remaining_stops = _select_stops_standard(remaining_intent, candidates)
            selected_stops.extend(remaining_stops)
        
        return selected_stops
    else:
        # Use standard selection
        return _select_stops_standard(intent, candidates)

def _select_stops_standard(intent: dict, candidates: list) -> list:
    """
    Standard Gemini stop selection (existing functionality)
    """
    system_rules = (
        "You are an expert route planner. "
        "Given a list of candidate places and user intent, select exactly one place per category from the user's requested 'place_types'. Each selected place must match the corresponding category."
        "Return a STRICT JSON array of place objects, sorted in the order they should be visited, matching the categories in 'place_types' from the user intent. "
        "For each category, only include one place in the returned list. Do not include multiple places of the same category. "
        "Choose places based on the following priorities: "
        "1) User intent (consider the user's specific mention of the place and their context). "
        "2) Proximity to the starting location (closer places are preferred). "
        "3) Rating (ONLY CONSIDER RATING IF PROXIMITY AND USER INTENT ARE EQUIVALENT. ALWAYS PRIORITIZE PROXIMITY AND USER INTENT FIRST). "
        "The last place in the returned list must match the 'last_destination' from the intent. "
        "If a category has no matching candidates, include the most relevant option from the available candidates. "
        "No extra text. No markdown. No code fences."
    )

    # Convert PlaceCandidate objects to dictionaries if needed
    candidates_dict = []
    for candidate in candidates:
        if hasattr(candidate, "__dict__"):
            # Convert Pydantic model to dict
            candidates_dict.append(
                candidate.dict() if hasattr(candidate, "dict") else candidate.__dict__
            )
        else:
            # Already a dictionary
            candidates_dict.append(candidate)

    prompt = f"{system_rules}\n User intent: {json.dumps(intent)}\n Candidate places: {json.dumps(candidates_dict)}"

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    print(f"Gemini raw response for select_stops: {response.text}")

    # Parse the JSON string response into a Python list
    stops = json.loads(response.text)
    return stops
