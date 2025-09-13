"""
Google Places service for sidequest functionality
This provides compatibility with the activity service and enhanced features.
"""

from services.activity_service import fetch_google_places

def search(intent):
    """
    Search for places based on user intent.
    This integrates with the activity service for enhanced place discovery.
    
    Args:
        intent: Dictionary containing location and other search parameters
        
    Returns:
        List of place candidates in the format expected by sidequest functionality
    """
    # Extract location from intent (default to Waterloo if not provided)
    location = intent.get("location", {"lat": 43.4643, "lon": -80.5204})
    
    # Fetch places using the existing activity service
    places = fetch_google_places(location["lat"], location["lon"])
    
    # Transform to the format expected by sidequest functionality
    candidates = []
    for place in places:
        if "structured" in place:
            candidate = place["structured"].copy()
            # Ensure we have the required fields
            if "name" not in candidate and "title" in candidate:
                candidate["name"] = candidate["title"]
            candidates.append(candidate)
    
    return candidates
