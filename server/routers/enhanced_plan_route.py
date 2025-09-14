"""
Enhanced plan route router that integrates RAG keyword checking
This extends the existing functionality with user keyword analysis
"""
import os
import json
import uuid
import shutil
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel

from schemas.plan_route_audio import PlanRouteAudioResponse
from services import speech_to_text, google_places
from services.enhanced_llm_service import parse_intent_with_rag, select_stops

router = APIRouter()

AUDIO_FILES_DIR = "audiofiles"

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
    """
    Build places search intent, filtering out personal locations that don't need Google Places search
    """
    # Extract non-personal place types for Google Places search
    place_types = intent.get("place_types", [])
    google_place_types = []
    
    for pt in place_types:
        if isinstance(pt, dict) and pt.get("source") == "user_keyword":
            # Skip personal locations - they don't need Google Places search
            continue
        else:
            # Include standard place types for Google Places search
            google_place_types.append(pt)
    
    return {
        "queries": google_place_types,
        "categories": google_place_types,
        "lat": lat,
        "lng": lng,
        "radius_m": intent.get("search_radius_meters", 10_000),
    }

def _pipeline_from_text_enhanced(
    text: str, 
    lat: Optional[float], 
    lng: Optional[float],
    auth0_user_id: Optional[str] = None
) -> PlanRouteAudioResponse:
    """
    Enhanced pipeline: parse intent with RAG -> search places -> select stops -> build response.
    """
    starting_location = (
        f"latitude:{lat},longitude:{lng}"
        if (lat is not None and lng is not None)
        else None
    )

    user_location = None
    if lat is not None and lng is not None:
        user_location = {"lat": lat, "lng": lng}

    # Enhanced intent parsing with RAG
    intent = parse_intent_with_rag(
        starting_location=starting_location,
        text=text,
        auth0_user_id=auth0_user_id,
        user_location=user_location
    )

    # Places intent (only for non-personal locations)
    places_intent = _build_places_intent(intent, lat, lng)

    # Google Places candidates (only if we have non-personal place types)
    candidates = []
    if places_intent.get("queries"):
        candidates = google_places.search(places_intent)

    # Enhanced stop selection (prioritizes personal locations)
    stops = select_stops(intent, candidates)

    # Build enhanced response message
    personal_locations = intent.get("personal_locations", [])
    unmatched_suggestions = intent.get("unmatched_suggestions", [])
    
    message_parts = []
    if personal_locations:
        message_parts.append(f"Found {len(personal_locations)} personal locations")
    if stops:
        message_parts.append(f"Found {len(stops)} total stops")
    if unmatched_suggestions:
        message_parts.append(f"Need clarification on {len(unmatched_suggestions)} locations")
    
    message = ", ".join(message_parts) if message_parts else "Processing complete"

    # Enhanced response with additional metadata
    response = PlanRouteAudioResponse(
        stops=stops,
        status="success",
        transcribed_text=text,
        message=message,
    )
    
    # Add enhanced metadata (this extends the response beyond the schema)
    response_dict = response.dict()
    response_dict["enhanced_metadata"] = {
        "personal_locations": personal_locations,
        "unmatched_suggestions": unmatched_suggestions,
        "has_personal_locations": intent.get("has_personal_locations", False),
        "rag_matches": intent.get("rag_matches", [])
    }
    
    return response_dict

# -----------------------------
# Enhanced Voice Route
# -----------------------------
@router.post("/enhanced-plan-route-audio", tags=["enhanced"])
async def enhanced_plan_route_audio(
    audio: UploadFile = File(...),
    location: Optional[str] = Form(None),
    auth0_user_id: Optional[str] = Form(None)
):
    """
    Enhanced audio route processing with RAG keyword checking.
    Checks user keywords before falling back to standard Google Places search.
    """
    try:
        print(f"🎵 === STARTING ENHANCED AUDIO PROCESSING ===")
        print(f"🎵 Audio filename: {audio.filename}")
        print(f"🎵 Auth0 User ID: {auth0_user_id}")
        
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

        # Reset file pointer for transcription
        audio.file.seek(0)
        
        # Transcribe
        print(f"🎤 Starting transcription...")
        text = speech_to_text.transcribe(audio)
        print(f"📝 Transcription complete: {text}")

        # Run enhanced pipeline
        print(f"🔄 Starting enhanced pipeline...")
        result = _pipeline_from_text_enhanced(
            text=text, 
            lat=lat, 
            lng=lng, 
            auth0_user_id=auth0_user_id
        )
        print(f"✅ Enhanced pipeline complete")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing enhanced audio upload: {e}",
        )

# -----------------------------
# Enhanced Text Route
# -----------------------------
class EnhancedPlanRouteTextRequest(BaseModel):
    text: str
    location: Optional[Dict[str, Any]] = None
    auth0_user_id: Optional[str] = None

@router.post("/enhanced-plan-route-text", tags=["enhanced"])
async def enhanced_plan_route_text(payload: EnhancedPlanRouteTextRequest):
    """
    Enhanced text route processing with RAG keyword checking.
    Checks user keywords before falling back to standard Google Places search.
    """
    try:
        lat = None
        lng = None
        if payload.location:
            lat = payload.location.get("lat") or payload.location.get("latitude")
            lng = payload.location.get("lng") or payload.location.get("longitude")
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None

        return _pipeline_from_text_enhanced(
            text=payload.text, 
            lat=lat, 
            lng=lng, 
            auth0_user_id=payload.auth0_user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing enhanced text route: {e}",
        )

# -----------------------------
# Comparison Endpoint
# -----------------------------
@router.post("/compare-enhanced-vs-standard", tags=["enhanced"])
async def compare_enhanced_vs_standard(payload: EnhancedPlanRouteTextRequest):
    """
    Compare enhanced RAG-based parsing with standard Gemini parsing
    """
    try:
        lat = None
        lng = None
        if payload.location:
            lat = payload.location.get("lat") or payload.location.get("latitude")
            lng = payload.location.get("lng") or payload.location.get("longitude")
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None

        # Enhanced result
        enhanced_result = _pipeline_from_text_enhanced(
            text=payload.text, 
            lat=lat, 
            lng=lng, 
            auth0_user_id=payload.auth0_user_id
        )

        # Standard result (import here to avoid circular imports)
        from services.llm_service import parse_intent, select_stops as select_stops_standard
        from routers.plan_route_audio import _pipeline_from_text

        standard_result = _pipeline_from_text(text=payload.text, lat=lat, lng=lng)

        return {
            "input": {
                "text": payload.text,
                "location": {"lat": lat, "lng": lng},
                "auth0_user_id": payload.auth0_user_id
            },
            "enhanced_result": enhanced_result,
            "standard_result": standard_result,
            "comparison": {
                "enhanced_has_personal_locations": enhanced_result.get("enhanced_metadata", {}).get("has_personal_locations", False),
                "enhanced_stops_count": len(enhanced_result.get("stops", [])),
                "standard_stops_count": len(standard_result.get("stops", [])),
                "personal_locations_found": len(enhanced_result.get("enhanced_metadata", {}).get("personal_locations", [])),
                "unmatched_suggestions": len(enhanced_result.get("enhanced_metadata", {}).get("unmatched_suggestions", []))
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}",
        )
