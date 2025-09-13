from typing import List, Optional
from pydantic import BaseModel

# ...existing code...

class Location(BaseModel):
    lat: float
    lng: float
    
# --- Plan Route Audio Response ---
class PlaceStop(BaseModel):
    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    types: List[str]
    google_maps_uri: Optional[str] = None
    website_uri: Optional[str] = None
    business_status: Optional[str] = None

class PlanRouteAudioResponse(BaseModel):
    stops: List[PlaceStop]
    status: str
    transcribed_text: str
    message: str

# ...existing code...

class GoogleDirectionsRequest(BaseModel):
    audio_file_path: str
    starting_location: Location  # Use the Location model defined above