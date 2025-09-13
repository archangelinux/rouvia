from typing import List, Optional
from pydantic import BaseModel

# --- Location ---
class Location(BaseModel):
    lat: float
    lng: float

# --- Distance / Duration ---
class DistanceDuration(BaseModel):
    text: str      # e.g., "2.1 km" or "7 mins"
    value: int     # distance in meters or duration in seconds

# --- Step ---
class Step(BaseModel):
    start_location: Location
    end_location: Location
    distance: DistanceDuration
    duration: DistanceDuration
    html_instructions: Optional[str] = None  # turn by turn instruction
    travel_mode: str
    polyline: Optional[str] = None          # Google encoded polyline for this step

# --- Leg ---
class Leg(BaseModel):
    start_address: str
    end_address: str
    start_location: Location
    end_location: Location
    distance: DistanceDuration
    duration: DistanceDuration
    steps: List[Step]

# --- Overview Polyline ---
class OverviewPolyline(BaseModel):
    points: str

# --- Route ---
class Route(BaseModel):
    summary: str
    legs: List[Leg]
    overview_polyline: OverviewPolyline
    bounds: Optional[dict] = None  # northeast & southwest coordinates

# --- Top-level response ---
class GoogleDirectionsResponse(BaseModel):
    routes: List[Route]
    status: str

# Example of expected JSON structure (you should be able to give this to mapbox):
# {
#   "routes": [
#     {
#       "summary": "Main St to University Ave",
#       "legs": [
#         {
#           "start_address": "...",
#           "end_address": "...",
#           "distance": { "text": "2.1 km", "value": 2100 },
#           "duration": { "text": "7 mins", "value": 420 },
#           "steps": [
#             {
#               "distance": { "text": "0.5 km", "value": 500 },
#               "duration": { "text": "2 mins", "value": 120 },
#               "start_location": { "lat": 43.4688, "lng": -80.5400 },
#               "end_location": { "lat": 43.4690, "lng": -80.5410 },
#               "polyline": { "points": "abcxyz..." },
#               "travel_mode": "DRIVING"
#             },
#             ...
#           ]
#         }
#       ],
#       "overview_polyline": { "points": "..." },
#       "bounds": { "northeast": {...}, "southwest": {...} }
#     }
#   ],
#   "status": "OK"
# }

