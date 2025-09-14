from google import genai
import os
import json
import re
from services.mongodb_service import mongodb_service


def _get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


def _get_user_keywords(user_id: str) -> dict:
    """
    Get user context including preferences and keywords from MongoDB
    """
    if not user_id:
        print(f"[LLM] No user_id provided")
        return {}
    
    try:
        print(f"[LLM] Looking up user profile for auth0_user_id: {user_id}")
        # Use auth0_user_id as the field name for the lookup
        profile = mongodb_service.get_user_profile_by_auth0_id(user_id)
        
        # Debug: Print the complete profile data
        print(f"[LLM] Complete user profile from MongoDB: {profile}")
        
        if not profile:
            print(f"[LLM] No profile found for auth0_user_id: {user_id}")
            return {}
        
        keywords = profile.get("keywords", {})
        print(f"[LLM] Extracted keywords: {keywords}")
        
        return {
            "keywords": keywords,
        }
    except Exception as e:
        print(f"Error getting user context: {e}")
        return {}


def _resolve_personalized_locations(text: str, user_context: dict) -> str:
    """
    Replace personalized keywords with actual addresses from user preferences
    Keywords format: {"home": "Society 145", "work": "51 Breithaupt St, Kitchener, ON", ...}
    """
    keywords = user_context.get("keywords", {})
    
    if not keywords:
        print("[LLM] No keywords found for user")
        return text
    
    print(f"[LLM] Available keywords: {list(keywords.keys())}")
    
    resolved_text = text
    
    for keyword, address in keywords.items():
        keyword_lower = keyword.lower()
        
        # Check if keyword appears in the text (case-insensitive)
        if keyword_lower in text.lower():
            # Replace the keyword with the actual address
            resolved_text = re.sub(
                re.escape(keyword), 
                str(address), 
                resolved_text, 
                flags=re.IGNORECASE
            )
            
            print(f"[LLM] Resolved '{keyword}' to '{address}'")
    
    return resolved_text


def parse_intent(starting_location: str, text: str, user_id: str = None) -> dict:
    """
    Use Gemini to parse user intent from transcribed text with keyword resolution.
    """
    print(f"[LLM] parse_intent called with user_id: {user_id}")
    print(f"[LLM] Original text: '{text}'")
    
    # Get user context and resolve personalized locations
    user_context = _get_user_keywords(user_id) if user_id else {}
    resolved_text = _resolve_personalized_locations(text, user_context)
    
    print(f"[LLM] Resolved text: '{resolved_text}'")
    
    # Add available keywords to system rules for better understanding
    keywords_info = ""
    if user_context.get("keywords"):
        keywords_list = list(user_context["keywords"].keys())
        keywords_info = f"\nUser has these personalized location keywords: {', '.join(keywords_list)}"
        print(f"[LLM] Keywords available: {keywords_list}")
    
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

    prompt = (
        f"{system_rules}{keywords_info}\n Starting location: {starting_location}\n User text: {resolved_text}"
    )

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    print(f"[LLM] Gemini response: {response.text}")

    # Parse the JSON string response into a Python dict
    intent_data = json.loads(response.text)
    return intent_data


def select_stops(intent: dict, candidates: list, user_id: str = None) -> list:
    """
    Use Gemini to select and rank stops from candidate places based on user intent.

    Args:
        intent: Parsed intent dictionary from parse_intent()
        candidates: List of candidate places from Google Places API
        user_id: User's Auth0 ID for accessing personalized preferences
    Returns:
        list: Selected and ranked stops as a list of place dictionaries
    """
    # Get user context for personalized recommendations
    user_context = _get_user_keywords(user_id) if user_id else {}
    
    system_rules = (
        "You are an expert route planner. "
        "Given a list of candidate places and user intent, select exactly one place per category from the user's requested 'place_types'. Each selected place must match the corresponding category."
        "Return a STRICT JSON array of place objects, sorted in the order they should be visited, matching the categories in 'place_types' from the user intent. "
        "You will parse location requests and convert keywords to actual addresses. "
        "The user may use personalized keywords for locations which have been resolved to actual addresses in the text."
        "For each category, only include one place in the returned list. Do not include multiple places of the same category. "
        "Choose places based on the following priorities: "
        "1) User intent (consider the user’s specific mention of the place and their context). "
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


if __name__ == "__main__":
    sample_starting_location = "University of Waterloo"
    sample_text = "I want to go to a coffee shop and then visit a museum."
    intent = parse_intent(sample_starting_location, sample_text)
    print("Parsed Intent:", intent)
