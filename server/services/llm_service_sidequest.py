"""
LLM service for sidequest functionality
This provides enhanced intent parsing and stop selection for sidequest features.
"""
from typing import Dict, List, Any
import json

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
