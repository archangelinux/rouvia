# server/main.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env robustly (works whether .env is in server/ or repo root)
load_dotenv()  # tries current working dir
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
import uvicorn
from routers import plan_route_audio, sidequest, user_profile, cohere_rag_experimental
from services import google_places  # ← now this sees the env var loaded above

app = FastAPI(
    title="Rouvia API",
    description="API for the Rouvia application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
origins = [
    "http://localhost:3000",  # Allow frontend to access
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(user_profile.router, prefix="", tags=["user_profile"])
app.include_router(cohere_rag_experimental.router, prefix="", tags=["experimental"])


class DebugIntent(BaseModel):
    queries: List[str]
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_m: Optional[int] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None
    max_results: Optional[int] = 10


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
