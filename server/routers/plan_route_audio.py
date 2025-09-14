# routers/plan_route_audio.py
# Accepts multipart audio uploads (for voice) and a JSON text route (for typed input)

import os
import json
import uuid
import shutil
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel

from schemas.plan_route_audio import PlanRouteAudioResponse
from services import speech_to_text, llm_service, google_places

router = APIRouter()

AUDIO_FILES_DIR = "audiofiles"
# os.makedirs(AUDIO_FILES_DIR, exist_ok=True)


# -----------------------------
# Helpers
# -----------------------------
def _parse_location_json(
    location_str: Optional[str],
) -> Tuple[Optional[float], Optional[float]]:
    """
    Accepts a JSON string or None. Supports keys:
    - { latitude, longitude }  (frontend browser geolocation)
    - { lat, lng }             (alt form)
    Returns (lat, lng) as floats or (None, None).
    """
    if not location_str:
        return None, None
    try:
        payload = json.loads(location_str)
    except json.JSONDecodeError:
        return None, None

    lat = payload.get("lat")
    if lat is None:
        lat = payload.get("latitude")

    lng = payload.get("lng")
    if lng is None:
        lng = payload.get("longitude")

    try:
        return (
            float(lat) if lat is not None else None,
            float(lng) if lng is not None else None,
        )
    except (TypeError, ValueError):
        return None, None


def _build_places_intent(
    intent: Dict[str, Any], lat: Optional[float], lng: Optional[float]
) -> Dict[str, Any]:
    return {
        "queries": intent.get("place_types", []),
        "categories": intent.get("place_types", []),
        "lat": lat,
        "lng": lng,
        "radius_m": intent.get("search_radius_meters", 10_000),
    }


def _pipeline_from_text(
    text: str, lat: Optional[float], lng: Optional[float], user_id: Optional[str] = None
) -> PlanRouteAudioResponse:
    """
    Shared pipeline: parse intent -> search places -> select stops -> build response.
    """
    starting_location = (
        f"latitude:{lat},longitude:{lng}"
        if (lat is not None and lng is not None)
        else None
    )

    print(f"🔄 Pipeline starting with user_id: {user_id}")

    # 2) LLM parse intent with user_id for keyword resolution
    intent = llm_service.parse_intent(starting_location, text, user_id)

    # 3) Places intent
    places_intent = _build_places_intent(intent, lat, lng)

    # 4) Google Places candidates
    candidates = google_places.search(places_intent)

    # 5) LLM selects actual stops with user_id for personalized preferences
    stops = llm_service.select_stops(intent, candidates, user_id)

    # 6) Response
    return PlanRouteAudioResponse(
        stops=stops,
        status="success",
        transcribed_text=text,
        message=f"Found {len(stops)} stops for your route",
    )


# -----------------------------
# 1) Voice route: multipart/form-data
# -----------------------------
@router.post("/plan-route-audio", response_model=PlanRouteAudioResponse)
async def plan_route_audio(
    audio: UploadFile = File(...),  # matches your FormData key "audio"
    location: Optional[str] = Form(
        None
    ),  # optional JSON string {"latitude":..., "longitude":...}
    user_id: Optional[str] = Form(None),  # Add user_id support
):
    """
    Accepts an audio file upload, optional location JSON, and optional user_id.
    Saves the file, transcribes with Whisper, runs intent->places->stops pipeline, returns final response.
    """

    try:
        print(f"🎵 === STARTING AUDIO PROCESSING ===")
        print(f"🎵 Audio filename: {audio.filename}")
        print(f"🎵 Audio content type: {audio.content_type}")
        print(f"🎵 User ID: {user_id}")
        
        # Parse optional location first
        lat, lng = _parse_location_json(location)
        print(f"🗺️ Parsed location: lat={lat}, lng={lng}")

        audio.file.seek(0)
        
        _, ext = os.path.splitext(audio.filename or "")
        ext = ext or ".wav"
        saved_name = f"{uuid.uuid4()}{ext}"
        saved_path = os.path.join(AUDIO_FILES_DIR, saved_name)
        
        print(f"💾 Saving to path: {saved_path}")
        with open(saved_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        
        print(f"✅ File saved successfully")
        print(f"📊 File size: {os.path.getsize(saved_path)} bytes")

        # 2) Reset file pointer again for transcription
        audio.file.seek(0)
        
        # 3) Transcribe
        print(f"🎤 Starting transcription...")
        text = speech_to_text.transcribe(audio)
        print(f"📝 Transcription complete: {text}")

        # 4) Run the pipeline with user_id
        print(f"🔄 Starting pipeline with user_id: {user_id}")
        result = _pipeline_from_text(text=text, lat=lat, lng=lng, user_id=user_id)
        print(f"✅ Pipeline complete")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio upload: {e}",
        )


# -----------------------------
# 2) Text route: application/json (for typed chat)
# -----------------------------
class PlanRouteTextRequest(BaseModel):
    text: str
    location: Optional[Dict[str, Any]] = (
        None  # supports {latitude, longitude} or {lat, lng}
    )
    user_id: Optional[str] = None  # Add user_id support


@router.post("/plan-route-text", response_model=PlanRouteAudioResponse)
async def plan_route_text(payload: PlanRouteTextRequest):
    """
    Accepts typed text, optional location JSON, and optional user_id via application/json.
    Runs the same pipeline used by the audio route (skipping transcription).
    """
    try:
        print(f"📝 Text route with user_id: {payload.user_id}")
        
        lat = None
        lng = None
        if payload.location:
            lat = payload.location.get("lat") or payload.location.get("latitude")
            lng = payload.location.get("lng") or payload.location.get("longitude")
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None

        return _pipeline_from_text(text=payload.text, lat=lat, lng=lng, user_id=payload.user_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text route: {e}",
        )
