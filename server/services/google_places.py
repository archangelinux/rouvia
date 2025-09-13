"""
Google Places service for backward compatibility with plan_route.py
This is a minimal wrapper to make the existing plan_route.py work.
"""

from services.activity_service import fetch_google_places

def search(intent):
    """
    Search for places based on user intent.
    This is a compatibility wrapper for the existing plan_route.py.
    """
    # Extract location from intent (default to Waterloo if not provided)
    location = intent.get("location", {"lat": 43.4643, "lon": -80.5204})
    
    # Fetch places using the existing activity service
    places = fetch_google_places(location["lat"], location["lon"])
    
    # Transform to the format expected by plan_route.py
    candidates = []
    for place in places:
        if "structured" in place:
            candidate = place["structured"].copy()
            # Ensure we have the required fields
            if "name" not in candidate and "title" in candidate:
                candidate["name"] = candidate["title"]
            candidates.append(candidate)
    
    return candidates
