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
    "You will first check if the user specifies specific locations. If so, prioritize those locations over general categories. "
    "If specific locations are provided, return them directly. If only categories are given, proceed to select places based on those categories. "
    "Return a STRICT JSON object with exactly three keys: "
    "1) 'place_types': an array of Google Places API place types (lowercase snake_case) that represents the user's intended destinations. If specific locations are mentioned, use those instead of categories. "
    "2) 'last_destination': a string representing the last destination the user wants to visit. This should be the final destination in 'place_types'. If specific locations are given, this will be the last specified location. "
    "3) 'search_radius_meters': an integer representing the search radius in meters from the starting location. If no specific locations are mentioned, default to 10000 meters. "
    "If the user specifies only one destination, 'last_destination' should match that destination, and 'place_types' should contain only that destination. "
    "No extra text. No markdown. No code fences."
)

    prompt = f"{system_rules}\n Starting location: {starting_location}\n User text: {text}"

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
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
    "Given a list of candidate places and user intent, select exactly one place per category from the user’s requested 'place_types'. Each selected place must match the corresponding category."
    "Return a STRICT JSON array of place objects, sorted in the order they should be visited, matching the categories in 'place_types' from the user intent. "
    "For each category, only include one place in the returned list. Do not include multiple places of the same category. "
    "Choose places based on the following priorities: "
    "1) User intent (consider the user’s specific mention of the place and their context). "
    "2) Rating (higher-rated places are preferred). "
    "3) Proximity to the starting location (closer places are preferred). "
    "The last place in the returned list must match the 'last_destination' from the intent. "
    "If a category has no matching candidates, include the most relevant option from the available candidates. "
    "No extra text. No markdown. No code fences."
)

    # Convert PlaceCandidate objects to dictionaries if needed
    candidates_dict = []
    for candidate in candidates:
        if hasattr(candidate, '__dict__'):
            # Convert Pydantic model to dict
            candidates_dict.append(candidate.dict() if hasattr(candidate, 'dict') else candidate.__dict__)
        else:
            # Already a dictionary
            candidates_dict.append(candidate)

    prompt = f"{system_rules}\n User intent: {json.dumps(intent)}\n Candidate places: {json.dumps(candidates_dict)}"

    client = _get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
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
