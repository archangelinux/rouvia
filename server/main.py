from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import datetime
import uvicorn

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

# In-memory database for demonstration
users_db: List[Dict[str, Any]] = []
next_user_id = 1

class UserCreate(BaseModel):
    name: str
    email: str

class User(UserCreate):
    id: int
    created_at: datetime.datetime

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

@app.post("/api/users", summary="Create a new user", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    global next_user_id
    new_user = User(id=next_user_id, created_at=datetime.datetime.now(), **user.dict())
    users_db.append(new_user.dict())
    next_user_id += 1
    return new_user

@app.get("/api/users", summary="Get all users", response_model=List[User])
async def get_users():
    return users_db

@app.get("/api/users/{user_id}", summary="Get a user by ID", response_model=User)
async def get_user(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/api/users/{user_id}", summary="Delete a user by ID")
async def delete_user(user_id: int):
    user_index = -1
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            user_index = i
            break
    if user_index == -1:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users_db.pop(user_index)
    return {"message": f"User {deleted_user['name']} deleted successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
