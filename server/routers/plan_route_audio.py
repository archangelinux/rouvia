# first we ask whisper to transcribe voice input
# then we send the transcription to gemini for types of places to search on google places
# then we use the places to give to google maps to get a list of locations
# then we send the list of locations to gemini to rank them and give a final json to give to gemini for routing
# then we send the final json to google places to get a route
# finally we send the route to the frontend for mapbox to render

import os
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from server.schemas.plan_route_audio import GoogleDirectionsResponse
from services import speech_to_text
from fastapi.responses import JSONResponse
import shutil
from datetime import datetime
import uuid

# Import your services (uncomment when you have these implemented)
# from services import llm_service, google_places, route_optimizer

router = APIRouter()

AUDIO_FILES_DIR = "audiofiles"
os.makedirs(AUDIO_FILES_DIR, exist_ok=True)

@router.post("/plan-route-audio", response_model=GoogleDirectionsResponse)
async def plan_route(audio: UploadFile = File(...)):
    try:
        # Use the filename sent from the frontend
        filename = audio.filename
        if not filename:
            # Fallback if no filename provided
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"voice_{timestamp}_{unique_id}.wav"
        
        file_path = os.path.join(AUDIO_FILES_DIR, filename)
        
        # Save the audio file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        print(f"Audio file saved: {file_path}")

        # 1. Transcribe audio - pass the file path instead of UploadFile object
        text = speech_to_text.transcribe(file_path)
        
        # 2. Parse intent with LLM
        intent = llm_service.parse_intent(text)
        
        # 3. Get candidate places from Google Places API
        candidates = google_places.search(intent)
        
        # 4. LLM selects actual stops
        stops = llm_service.select_stops(intent, candidates)
        
        # 5. Optimize route
        route = route_optimizer.compute_route(stops)
        
        # 6. Return optimized route to frontend
        return route

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio file: {str(e)}"
        )