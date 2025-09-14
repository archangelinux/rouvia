"""
Experimental Cohere RAG router for location keyword parsing
This provides new endpoints to test RAG-based location parsing without affecting existing functionality
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from services.cohere_rag_location_parser import parse_user_text_with_rag, get_user_location_keywords_stats

router = APIRouter()

class RAGParseRequest(BaseModel):
    user_text: str
    auth0_user_id: str
    context_location: Optional[Dict[str, float]] = None

class RAGParseResponse(BaseModel):
    matched_keywords: List[str]
    location_data: List[Dict[str, Any]]
    confidence_scores: List[float]
    parsed_intent: Dict[str, Any]
    user_keywords_count: int
    error: Optional[str] = None

class UserStatsResponse(BaseModel):
    total_keywords: int
    keyword_list: List[str]
    location_types: Dict[str, int]
    recent_additions: List[Dict[str, Any]]
    error: Optional[str] = None

@router.post("/experimental/rag-parse", response_model=RAGParseResponse, tags=["experimental"])
async def parse_text_with_rag(request: RAGParseRequest):
    """
    Parse user text using Cohere RAG to find location keywords from user's database
    
    This is an experimental endpoint that uses RAG to understand user text
    and match it against their personal location keyword database.
    """
    try:
        result = parse_user_text_with_rag(
            user_text=request.user_text,
            auth0_user_id=request.auth0_user_id,
            context_location=request.context_location
        )
        
        return RAGParseResponse(
            matched_keywords=result.get("matched_keywords", []),
            location_data=result.get("location_data", []),
            confidence_scores=result.get("confidence_scores", []),
            parsed_intent=result.get("parsed_intent", {}),
            user_keywords_count=result.get("user_keywords_count", 0),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG parsing failed: {str(e)}"
        )

@router.get("/experimental/user-keywords-stats/{auth0_user_id}", response_model=UserStatsResponse, tags=["experimental"])
async def get_user_keyword_stats(auth0_user_id: str):
    """
    Get statistics about a user's location keyword database
    
    Returns information about the user's stored keywords, their types,
    and recent additions for analysis and debugging.
    """
    try:
        stats = get_user_location_keywords_stats(auth0_user_id)
        
        return UserStatsResponse(
            total_keywords=stats.get("total_keywords", 0),
            keyword_list=stats.get("keyword_list", []),
            location_types=stats.get("location_types", {}),
            recent_additions=stats.get("recent_additions", []),
            error=stats.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )

@router.post("/experimental/rag-compare", tags=["experimental"])
async def compare_rag_vs_current(request: RAGParseRequest):
    """
    Compare RAG parsing results with current Gemini-based parsing
    
    This endpoint runs both parsing methods on the same input and returns
    a comparison for analysis and testing.
    """
    try:
        # Get RAG results
        rag_result = parse_user_text_with_rag(
            user_text=request.user_text,
            auth0_user_id=request.auth0_user_id,
            context_location=request.context_location
        )
        
        # Get current Gemini results (import here to avoid circular imports)
        from services.llm_service import parse_intent
        
        # Create a mock starting location for Gemini
        starting_location = "Current Location"
        if request.context_location:
            starting_location = f"{request.context_location['lat']}, {request.context_location['lng']}"
        
        gemini_result = parse_intent(starting_location, request.user_text)
        
        return {
            "input": {
                "user_text": request.user_text,
                "auth0_user_id": request.auth0_user_id,
                "context_location": request.context_location
            },
            "rag_results": {
                "matched_keywords": rag_result.get("matched_keywords", []),
                "location_data": rag_result.get("location_data", []),
                "confidence_scores": rag_result.get("confidence_scores", []),
                "parsed_intent": rag_result.get("parsed_intent", {}),
                "user_keywords_count": rag_result.get("user_keywords_count", 0)
            },
            "gemini_results": {
                "place_types": gemini_result.get("place_types", []),
                "last_destination": gemini_result.get("last_destination", ""),
                "search_radius_meters": gemini_result.get("search_radius_meters", 10000)
            },
            "comparison": {
                "rag_found_keywords": len(rag_result.get("matched_keywords", [])) > 0,
                "gemini_found_places": len(gemini_result.get("place_types", [])) > 0,
                "methods_differ": rag_result.get("matched_keywords", []) != gemini_result.get("place_types", [])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )

@router.get("/experimental/test-keywords", tags=["experimental"])
async def test_with_sample_keywords():
    """
    Test endpoint with sample user keywords for demonstration
    
    Creates a test user with sample keywords and demonstrates RAG parsing.
    """
    try:
        # Sample test data
        test_user_id = "test_rag_user"
        test_keywords = {
            "coffee": {
                "name": "Blue Bottle Coffee",
                "address": "123 Main St, San Francisco, CA",
                "lat": 37.7749,
                "lng": -122.4194,
                "place_id": "test_blue_bottle",
                "added_at": "2024-01-15T10:00:00Z"
            },
            "museum": {
                "name": "SF Museum of Modern Art",
                "address": "151 3rd St, San Francisco, CA",
                "lat": 37.7857,
                "lng": -122.4011,
                "place_id": "test_sfmoma",
                "added_at": "2024-01-10T14:30:00Z"
            },
            "park": {
                "name": "Golden Gate Park",
                "address": "Golden Gate Park, San Francisco, CA",
                "lat": 37.7694,
                "lng": -122.4862,
                "place_id": "test_gg_park",
                "added_at": "2024-01-05T09:15:00Z"
            }
        }
        
        # Add test keywords to user profile (this would normally be done through the user profile API)
        from services.user_profile_service import user_profiles_col
        from datetime import datetime
        
        # Create or update test user
        test_user = {
            "auth0_user_id": test_user_id,
            "email": "test@example.com",
            "keywords": test_keywords,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        user_profiles_col.update_one(
            {"auth0_user_id": test_user_id},
            {"$set": test_user},
            upsert=True
        )
        
        # Test RAG parsing with sample text
        test_texts = [
            "I want to go to the coffee shop",
            "Let's visit the museum today",
            "Can we go to the park for a walk?",
            "I need to find a good restaurant",
            "Show me places near Golden Gate"
        ]
        
        results = []
        for text in test_texts:
            result = parse_user_text_with_rag(text, test_user_id)
            results.append({
                "input_text": text,
                "matched_keywords": result.get("matched_keywords", []),
                "confidence_scores": result.get("confidence_scores", []),
                "reasoning": result.get("parsed_intent", {}).get("reasoning", "No reasoning provided")
            })
        
        return {
            "test_user_id": test_user_id,
            "sample_keywords": test_keywords,
            "test_results": results,
            "message": "Test completed successfully. Check results to see how RAG matches user text to their keywords."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )
