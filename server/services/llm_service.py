"""
LLM service for parsing user intent and selecting stops
"""
from typing import Dict, List, Any
import json
import os

# Gemini-based functions (from HEAD)
from google import genai

def _get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def parse_intent_gemini(starting_location: str, text: str) -> dict:
    """
    Use Gemini to parse user intent from transcribed text.
    
    Args:
        starting_location: The user's starting location as a string
        text: Transcribed text from user audio input

    Returns:
        dict: Parsed intent as a dictionary
    """

    system_rules = (
        "You extract destination CATEGORIES only. "
        "Return a STRICT JSON object with exactly three keys: "
        "1) 'place_types': an array of Google Places API place types (lowercase snake_case) that is sorted in the order that the user wants to go to. "
        "2) 'last_destination': a string that is the last element from 'place_types'. "
        "3) 'search_radius_meters': an integer representing the search radius in meters with the starting location as the center for all destinations. If there are no specific destinations mentioned, default to 10000 meters. "
        "If the user specifies only one destination, 'last_destination' is that destination. "
        "No extra text. No markdown. No code fences."
    )

    prompt = f"{system_rules}\n Starting location: {starting_location}\n User text: {text}"

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    print(f"Gemini raw response: {response.text}")
    
    # Parse the JSON string response into a Python dict
    intent_data = json.loads(response.text)
    return intent_data

def select_stops_gemini(intent: dict, candidates: list) -> list:
    """
    Use Gemini to select and rank stops from candidate places based on user intent.
    
    Args:
        intent: Parsed intent dictionary from parse_intent()
        candidates: List of candidate places from Google Places API
    Returns:
        list: Selected and ranked stops as a list of place dictionaries
    """
    system_rules = (
        "You are an expert route planner. "
        "Given a list of candidate places and user intent, order the best places to visit by intent, shortest route, and rating. "
        "Return a STRICT JSON array of place objects sorted in the order they should be visited. "
        "Each place object should be the same format as how the Google Places API returns place objects for the candidate places."
        "Only include places that match the user's requested categories in 'place_types' from the intent. "
        "make sure to include a place matching the 'last_destination' as the final place in the list. "
        "No extra text. No markdown. No code fences."
    )

    prompt = f"{system_rules}\n User intent: {json.dumps(intent)}\n Candidate places: {json.dumps(candidates)}"

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    print(f"Gemini raw response for select_stops: {response.text}")
    
    # Parse the JSON string response into a Python list
    stops = json.loads(response.text)
    return stops

# Enhanced parsing functions (from sidequest-and-database branch)
def parse_intent(text: str) -> Dict[str, Any]:
    """
    Parse user intent from transcribed text to extract comprehensive planning information
    
    Args:
        text: Transcribed text from audio
        
    Returns:
        Dict containing parsed intent information including time, location, interests, etc.
    """
    # Enhanced parsing logic - in a real implementation, this would use an LLM
    text_lower = text.lower()
    
    # Extract time information
    available_time_hours = 7  # Default
    if "hour" in text_lower:
        import re
        time_matches = re.findall(r'(\d+)\s*hour', text_lower)
        if time_matches:
            available_time_hours = int(time_matches[0])
    
    # Extract start time
    start_time = "10:00"  # Default
    if "morning" in text_lower:
        start_time = "09:00"
    elif "afternoon" in text_lower:
        start_time = "14:00"
    elif "evening" in text_lower:
        start_time = "18:00"
    
    # Extract interests
    interests = []
    interest_keywords = {
        "food": ["food", "eat", "restaurant", "cafe", "dining", "meal"],
        "culture": ["museum", "art", "culture", "gallery", "history", "heritage"],
        "nature": ["park", "nature", "outdoor", "hiking", "garden", "trail"],
        "entertainment": ["entertainment", "show", "concert", "theater", "movie"],
        "shopping": ["shopping", "mall", "store", "market", "boutique"],
        "sports": ["sports", "gym", "fitness", "exercise", "active"],
        "nightlife": ["bar", "club", "nightlife", "drinks", "party"]
    }
    
    for interest, keywords in interest_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            interests.append(interest)
    
    # Extract indoor/outdoor preference
    indoor_outdoor = "mixed"
    if any(word in text_lower for word in ["indoor", "inside", "inside"]):
        indoor_outdoor = "indoor"
    elif any(word in text_lower for word in ["outdoor", "outside", "outside"]):
        indoor_outdoor = "outdoor"
    
    # Extract energy level
    energy_level = 5  # Default medium
    if any(word in text_lower for word in ["relaxed", "chill", "calm", "peaceful"]):
        energy_level = 3
    elif any(word in text_lower for word in ["active", "energetic", "intense", "adventure"]):
        energy_level = 7
    
    # Extract budget (rough estimation)
    budget = 100  # Default
    if "cheap" in text_lower or "budget" in text_lower:
        budget = 50
    elif "expensive" in text_lower or "luxury" in text_lower:
        budget = 200
    
    # Default location (Waterloo, ON)
    location = {"lat": 43.4643, "lon": -80.5204}
    
    return {
        "available_time_hours": available_time_hours,
        "start_time": start_time,
        "interests": interests,
        "indoor_outdoor": indoor_outdoor,
        "energy_level": energy_level,
        "budget": budget,
        "location": location,
        "original_text": text
    }

def select_stops(intent: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Select actual stops from candidate places based on intent
    Note: This function is now primarily used for backward compatibility.
    The main activity selection is handled by the itinerary_generator.
    
    Args:
        intent: Parsed user intent
        candidates: List of candidate places from all sources
        
    Returns:
        List of selected stops (simplified selection for route optimization)
    """
    # Since we now use itinerary_generator for comprehensive selection,
    # this function provides a simplified fallback selection
    if not candidates:
        return []
    
    # Simple selection based on confidence scores
    structured_candidates = []
    for candidate in candidates:
        if "structured" in candidate:
            structured_candidates.append(candidate["structured"])
        else:
            structured_candidates.append(candidate)
    
    # Sort by confidence and return top candidates
    sorted_candidates = sorted(
        structured_candidates, 
        key=lambda x: x.get("confidence", 0), 
        reverse=True
    )
    
    # Return top 5 candidates as a reasonable default
    return sorted_candidates[:5]

# Backward compatibility aliases
def parse_intent_legacy(starting_location: str, text: str) -> dict:
    """Legacy function for backward compatibility with plan_route_audio.py"""
    return parse_intent_gemini(starting_location, text)

if __name__ == "__main__":
    sample_starting_location = "University of Waterloo"
    sample_text = "I want to go to a coffee shop and then visit a museum."
    intent = parse_intent_gemini(sample_starting_location, sample_text)
    print("Parsed Intent:", intent)
