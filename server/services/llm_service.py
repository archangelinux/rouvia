from google import genai
import os
import json

def _get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def parse_intent(starting_location: str, text: str) -> dict:
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

def select_stops(intent: dict, candidates: list) -> list:
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

if __name__ == "__main__":
    sample_starting_location = "University of Waterloo"
    sample_text = "I want to go to a coffee shop and then visit a museum."
    intent = parse_intent(sample_starting_location, sample_text)
    print("Parsed Intent:", intent)
