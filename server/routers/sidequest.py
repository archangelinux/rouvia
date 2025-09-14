from fastapi import APIRouter, HTTPException
from schemas.sidequest import SidequestRequest, SidequestResponse
from services.sidequest_service import fetch_and_prepare_sidequests
from services.user_profile_service import (
    get_saved_locations, 
    add_saved_location, 
    update_saved_location, 
    delete_saved_location,
    get_saved_location_by_id
)
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Pydantic models for saved locations
class Location(BaseModel):
    id: str
    name: str
    address: str

class LocationRequest(BaseModel):
    name: str
    address: str

class LocationUpdateRequest(BaseModel):
    name: str
    address: str

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
        user_id=request.user_id,
    )
    return results

# ===== SAVED LOCATIONS ENDPOINTS =====

@router.get("/saved-locations/{user_id}", response_model=List[Location])
async def get_user_saved_locations(user_id: str):
    """
    Get all saved locations for a user
    """
    locations = get_saved_locations(user_id)
    return locations

@router.post("/saved-locations/{user_id}", response_model=Location)
async def add_user_saved_location(user_id: str, location: LocationRequest):
    """
    Add a new saved location for a user
    """
    location_id = add_saved_location(user_id, location.name, location.address)
    return Location(id=location_id, name=location.name, address=location.address)

@router.put("/saved-locations/{user_id}/{location_id}", response_model=Location)
async def update_user_saved_location(user_id: str, location_id: str, location: LocationUpdateRequest):
    """
    Update an existing saved location for a user
    """
    success = update_saved_location(user_id, location_id, location.name, location.address)
    if success:
        return Location(id=location_id, name=location.name, address=location.address)
    else:
        raise HTTPException(status_code=404, detail="Location not found")

@router.delete("/saved-locations/{user_id}/{location_id}")
async def delete_user_saved_location(user_id: str, location_id: str):
    """
    Delete a saved location for a user
    """
    success = delete_saved_location(user_id, location_id)
    if success:
        return {"message": "Location deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Location not found")

@router.get("/saved-locations/{user_id}/{location_id}", response_model=Location)
async def get_user_saved_location(user_id: str, location_id: str):
    """
    Get a specific saved location for a user
    """
    location = get_saved_location_by_id(user_id, location_id)
    if location:
        return location
    else:
        raise HTTPException(status_code=404, detail="Location not found")
