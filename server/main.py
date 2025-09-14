# server/main.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env robustly (works whether .env is in server/ or repo root)
load_dotenv()  # tries current working dir
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

from fastapi import FastAPI, HTTPException, status, Body
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
import uvicorn
from routers import plan_route_audio, sidequest
from services import google_places  # ← now this sees the env var loaded above
from services.mongo import user_profiles_col
from mock_data import update_user_location, get_user_locations

app = FastAPI(
    title="Rouvia API",
    description="API for the Rouvia application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# MongoDB connection is handled in services.mongo

# CORS middleware
origins = [
    "http://localhost:3000",  # Allow frontend to access
    "http://localhost:3001", #allow frontend when docker occupies 3000
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    #allow_origins=origins,      # allow these origins
    allow_credentials=True,
    allow_methods=["*"],        # allow all HTTP methods
    allow_headers=["*"],        # allow all headers
)


@app.get("/", summary="Root endpoint", response_model=Dict[str, str])
async def read_root():
    return {"message": "Welcome to Rouvia API", "docs": "/docs"}


@app.get("/api/health", summary="Health check endpoint", response_model=Dict[str, Any])
async def health_check():
    return {
        "message": "Server is running!",
        "timestamp": datetime.datetime.now(),
        "status": "healthy",
    }


app.include_router(plan_route_audio.router, prefix="", tags=["plan_route"])
app.include_router(sidequest.router, prefix="", tags=["sidequest"])


class DebugIntent(BaseModel):
    queries: List[str]
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_m: Optional[int] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None
    max_results: Optional[int] = 10
'''
@app.post("/update-location/{user_id}")
def update_location(user_id: str, location: dict = Body(...)):
    """
    location example:
    {
        "name": "home",
        "coords": ["long", "lat"],
        "address": "123 Main St, City, State"
    }
    """
    try:
        # Prepare location data to store
        location_data = {
            "coords": location.get("coords", [0, 0]),
            "address": location.get("address", ""),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Try MongoDB first
        try:
            result = user_profiles_col.update_one(
                {"user_id": user_id},
                {"$set": {f"locations.{location['name']}": location_data}},
                upsert=True
            )
            return {"success": True, "modified": result.modified_count, "source": "mongodb"}
        except Exception as mongo_error:
            print(f"⚠️ MongoDB failed, using mock data: {mongo_error}")
            # Fallback to mock data
            update_user_location(user_id, location['name'], location_data)
            return {"success": True, "modified": 1, "source": "mock"}
            
    except Exception as e:
        print(f"❌ Error updating location: {e}")
        return {"success": False, "error": str(e)}

@app.get("/saved-locations/{user_id}")
def get_saved_locations(user_id: str):
    """
    Get all saved locations for a user
    """
    try:
        user_profile = user_profiles_col.find_one({"user_id": user_id})
        if not user_profile:
            return {"locations": {}}
        
        locations = user_profile.get("locations", {})
        return {"locations": locations}
    except Exception as e:
        print(f"❌ Error getting saved locations: {e}")
        return {"locations": {}, "error": str(e)}


'''
@app.post("/debug/places", tags=["debug"])
def debug_places(intent: DebugIntent):
    try:
        results = google_places.search(intent.model_dump())
        # return plain dicts for eyeballing
        return [r.model_dump(by_alias=False) for r in results]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
