# first we ask whisper to transcribe voice input
# then we send the transcription to gemini for types of places to search on google places
# then we use the places to give to google maps to get a list of locations (set center point as middle between 2 points, get all pois in radius)
# then we send the list of locations to gemini to rank them and give a final json to give to gemini for routing
# then we send the final json to google places to get a route
# finally we send the route to the frontend for mapbox to render

import os
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from schemas.plan_route_audio import PlanRouteAudioResponse, GoogleDirectionsRequest
from services import speech_to_text, llm_service, google_places
from fastapi.responses import JSONResponse
import shutil
from datetime import datetime
import uuid

# Import your services (uncomment when you have these implemented)
# from services import llm_service, google_places, route_optimizer

router = APIRouter()

AUDIO_FILES_DIR = "audiofiles"
os.makedirs(AUDIO_FILES_DIR, exist_ok=True)

# ...existing code...

@router.post("/plan-route-audio")
async def plan_route(input: GoogleDirectionsRequest):
    try:
        # Get the audio file path and location from the request
        filename = input.audio_file_path
        start_lat = input.starting_location.lat
        start_lng = input.starting_location.lng
        
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Audio file path is required"
            )

        file_path = os.path.join(AUDIO_FILES_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {filename}"
            )

        print(f"Processing audio file: {file_path}")
        print(f"Start location: {start_lat}, {start_lng}")

        # 1. Transcribe audio using the file path
        with open(file_path, "rb") as f:
            upload_file = UploadFile(filename=filename, file=f)
            text = speech_to_text.transcribe(upload_file)
        
        print(f"Transcribed text: {text}")

        # 2. Parse intent with LLM
        starting_location = f"latitude:{start_lat},longitude:{start_lng}"
        intent = llm_service.parse_intent(starting_location, text)
        print(f"Parsed intent: {intent}")

        # 3. Transform intent for Google Places API
        places_intent = {
            "queries": intent.get("place_types", []),
            "categories": intent.get("place_types", []),
            "lat": start_lat,
            "lng": start_lng,
            "radius_m": intent.get("search_radius_meters", 10000)
        }
        print(f"Places API intent: {places_intent}")

        # 4. Get candidate places from Google Places API
        candidates = google_places.search(places_intent)
        print(f"Found {len(candidates)} candidates")

        # 5. LLM selects actual stops
        stops = llm_service.select_stops(intent, candidates)
        print(f"Selected stops: {stops}")

        # 6. Return optimized route to frontend
        return PlanRouteAudioResponse(
            stops=stops,
            status="success",
            transcribed_text=text,
            message=f"Found {len(stops)} stops for your route"
        )

    except Exception as e:
        print(f"Error in plan_route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio file: {str(e)}",
        )

if __name__ == "__main__":
    import asyncio
    import traceback
    from fastapi import UploadFile

    async def test_route_planning():
        print("=== Plan Route Audio Test ===")

        # Check required environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        google_api_key = os.getenv("GOOGLE_CLOUD_API_KEY")

        print(f"🔍 OPENAI_API_KEY: {'SET' if openai_api_key else 'NOT SET'}")
        print(f"🔍 GEMINI_API_KEY: {'SET' if gemini_api_key else 'NOT SET'}")
        print(f"🔍 GOOGLE_CLOUD_API_KEY: {'SET' if google_api_key else 'NOT SET'}")

        if not openai_api_key or not gemini_api_key or not google_api_key:
            print("❌ One or more required environment variables are not set")
            return

        print("✅ Environment variables set correctly")

        # Test with example file
        example_file = "./services/example_audio.wav"
        print(f"\n🔍 Looking for: {example_file}")

        if os.path.exists(example_file):
            file_size = os.path.getsize(example_file)
            print(f"✅ Audio file found (size: {file_size} bytes)")

            try:
                print("🔄 Starting route planning...")
                
                # Create a test request object
                from schemas.plan_route_audio import Location
                test_request = GoogleDirectionsRequest(
                    audio_file_path="example_audio.wav",
                    starting_location=Location(lat=43.472135467199074, lng=-80.54468594453151)  # Waterloo coords
                )
                
                # Copy the example file to the expected location
                import shutil
                target_path = os.path.join(AUDIO_FILES_DIR, "example_audio.wav")
                shutil.copy2(example_file, target_path)
                
                result = await plan_route(test_request)

                if result:
                    print(f"✅ Route planning successful!")
                    print(f"📝 Result: {result}")
                else:
                    print("⚠️ Route planning returned empty result")

            except Exception as e:
                print(f"❌ Error during route planning: {str(e)}")
                traceback.print_exc()
        else:
            print("❌ Example audio file not found. Please provide a valid audio file to test.")

    # Run the async test
    asyncio.run(test_route_planning())