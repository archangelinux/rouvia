"""
User Profile API Router for Auth0 integration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from services.user_profile_service import (
    create_or_update_auth0_user_profile,
    add_keyword_location,
    get_user_keywords,
    get_user_profile_by_auth0_id,
    delete_keyword,
    migrate_existing_users_add_keywords
)

router = APIRouter(prefix="/api/user-profile", tags=["user-profile"])

# Pydantic models for request/response
class Auth0UserData(BaseModel):
    auth0_user_id: str
    email: str
    name: Optional[str] = None
    nickname: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class LocationData(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    place_id: Optional[str] = None

class KeywordLocationRequest(BaseModel):
    keyword: str
    location: LocationData

class KeywordLocationResponse(BaseModel):
    keyword: str
    location: LocationData
    added_at: str

@router.post("/create-or-update")
async def create_or_update_profile(user_data: Auth0UserData):
    """
    Create or update user profile from Auth0 data
    """
    try:
        profile = create_or_update_auth0_user_profile(
            auth0_user_id=user_data.auth0_user_id,
            email=user_data.email,
            name=user_data.name,
            nickname=user_data.nickname,
            picture=user_data.picture,
            given_name=user_data.given_name,
            family_name=user_data.family_name
        )
        
        return {
            "success": True,
            "message": "Profile created/updated successfully",
            "profile": {
                "auth0_user_id": profile["auth0_user_id"],
                "email": profile["email"],
                "name": profile.get("name"),
                "created_at": profile["created_at"],
                "last_login": profile.get("last_login")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create/update profile: {str(e)}")

@router.get("/{auth0_user_id}")
async def get_profile(auth0_user_id: str):
    """
    Get user profile by Auth0 user ID
    """
    try:
        profile = get_user_profile_by_auth0_id(auth0_user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "profile": {
                "auth0_user_id": profile["auth0_user_id"],
                "email": profile["email"],
                "name": profile.get("name"),
                "nickname": profile.get("nickname"),
                "picture": profile.get("picture"),
                "given_name": profile.get("given_name"),
                "family_name": profile.get("family_name"),
                "keywords": profile.get("keywords", {}),
                "visited_places": profile.get("visited_places", []),
                "preferences": profile.get("preferences", {}),
                "created_at": profile["created_at"],
                "last_login": profile.get("last_login"),
                "last_updated": profile["last_updated"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@router.post("/{auth0_user_id}/keywords")
async def add_keyword(auth0_user_id: str, request: KeywordLocationRequest):
    """
    Add a keyword -> location mapping
    """
    try:
        location_data = {
            "name": request.location.name,
            "address": request.location.address,
            "lat": request.location.lat,
            "lng": request.location.lng,
            "place_id": request.location.place_id
        }
        
        add_keyword_location(auth0_user_id, request.keyword, location_data)
        
        return {
            "success": True,
            "message": f"Keyword '{request.keyword}' added successfully",
            "keyword": request.keyword,
            "location": request.location
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add keyword: {str(e)}")

@router.get("/{auth0_user_id}/keywords")
async def get_keywords(auth0_user_id: str):
    """
    Get all keyword mappings for a user
    """
    try:
        keywords = get_user_keywords(auth0_user_id)
        
        return {
            "success": True,
            "keywords": keywords
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get keywords: {str(e)}")

@router.delete("/{auth0_user_id}/keywords/{keyword}")
async def remove_keyword(auth0_user_id: str, keyword: str):
    """
    Remove a keyword mapping
    """
    try:
        delete_keyword(auth0_user_id, keyword)
        
        return {
            "success": True,
            "message": f"Keyword '{keyword}' removed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove keyword: {str(e)}")

@router.get("/{auth0_user_id}/keywords/{keyword}")
async def get_keyword(auth0_user_id: str, keyword: str):
    """
    Get a specific keyword mapping
    """
    try:
        keywords = get_user_keywords(auth0_user_id)
        
        if keyword not in keywords:
            raise HTTPException(status_code=404, detail=f"Keyword '{keyword}' not found")
        
        return {
            "success": True,
            "keyword": keyword,
            "location": keywords[keyword]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get keyword: {str(e)}")

@router.post("/migrate-keywords")
async def migrate_keywords():
    """
    Migration endpoint to add keywords field to existing users
    """
    try:
        migrated_count = migrate_existing_users_add_keywords()
        
        return {
            "success": True,
            "message": f"Migration completed successfully",
            "migrated_users": migrated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
