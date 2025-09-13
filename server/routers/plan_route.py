# first we ask whisper to transcribe voicie input
# then we send the transcription to gemini for types of places to search on google places
# then we use the places to give to google maps to get a list of locations
# then we send the list of locations to gemini to rank them and give a final json to give to gemini for routing
# then we send the final json to google places to get a route
# finally we send the route to the frontend for mapbox to render

from fastapi import APIRouter, HTTPException, status, UploadFile
from schemas.plan_route import GoogleDirectionsResponse
from services import whisper_service, llm_service, google_places, route_optimizer

router = APIRouter()

@router.post("/plan-route", response_model=GoogleDirectionsResponse)
def plan_route(audio: UploadFile):
    # 1. Transcribe audio
    text = whisper_service.transcribe(audio)
    
    # 2. Parse intent with LLM
    intent = llm_service.parse_intent(text)
    
    # 3. Get candidate places from Google Places API
    candidates = google_places.search(intent)
    
    # 4. LLM selects actual stops
    stops = llm_service.select_stops(intent, candidates)
    
    # 5. Optimize route
    route = route_optimizer.compute_route(stops)
    
    # 6. Return optimized route to frontend
    return {"route": route, "stops": stops}