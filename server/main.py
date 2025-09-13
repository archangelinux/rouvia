from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import datetime
import uvicorn
from routers import plan_route, sidequest

app = FastAPI(
    title="Rouvia API",
    description="API for the Rouvia application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
origins = [
    "http://localhost:3000",  # Allow frontend to access
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1"
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
        "status": "healthy"
    }

app.include_router(plan_route.router, prefix="", tags=["plan_route"])
app.include_router(sidequest.router, prefix="/sidequest", tags=["sidequest"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
