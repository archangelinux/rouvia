from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Standardized interest categories
INTEREST_CATEGORIES = [
    "shopping", 
    "food", 
    "entertainment",
    "scenery",
]

class SidequestRequest(BaseModel):
    lat: float
    lon: float
    travel_distance: float = 5.0  # km
    start_time: str               # e.g., "09:00" - start time for sidequest
    end_time: str                 # e.g., "17:00" - end time for sidequest
    budget: Optional[float] = None
    interests: List[str] = []      # Must be from INTEREST_CATEGORIES
    energy: int = 5
    indoor_outdoor: Optional[str] = None  # "indoor", "outdoor", or None
    user_id: Optional[str] = None  # For tracking visited places

class SidequestActivity(BaseModel):
    title: str
    lat: float
    lon: float
    start_time: Optional[str]
    duration_hours: float
    cost: Optional[float]
    activity_type: str
    indoor_outdoor: str
    energy_level: int
    confidence: float

class ItineraryMetadata(BaseModel):
    activities_considered: int
    activities_selected: int
    activities_in_itinerary: int
    generation_time: Optional[str] = None

class SidequestResponse(BaseModel):
    itinerary: List[SidequestActivity]
    total_duration: float
    total_cost: float
    summary: str
    metadata: ItineraryMetadata