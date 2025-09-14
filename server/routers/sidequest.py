from fastapi import APIRouter
from schemas.sidequest import SidequestRequest, SidequestResponse
from services.sidequest_service import fetch_and_prepare_sidequests

router = APIRouter()

@router.post("/sidequest", response_model=SidequestResponse)
async def get_sidequests(request: SidequestRequest):
    """
    Sidequest endpoint: fetch real activities from all sources (Google Places, Luma, blogs),
    filter by user preferences, and return a structured itinerary.
    """
    print("lol")
    results = await fetch_and_prepare_sidequests(
        lat=request.lat,
        lon=request.lon,
        travel_distance=request.travel_distance,
        start_time=request.start_time,
        end_time=request.end_time,
        budget=request.budget,
        interests=request.interests,
        energy=request.energy,
        indoor_outdoor=request.indoor_outdoor,
        user_id=request.user_id
    )
    return results
