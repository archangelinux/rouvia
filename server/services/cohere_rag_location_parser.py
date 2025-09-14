"""
Cohere RAG-based location keyword parser for user database
Experimental service to parse user text and extract location keywords from their personal database
"""
import os
import json
from typing import Dict, List, Any, Optional
import cohere
from services.user_profile_service import get_user_keywords, get_user_profile_by_auth0_id
from services.mongo import user_profiles_col

# Initialize Cohere client
co = cohere.Client(os.getenv("COHERE_API_KEY"))

class CohereRAGLocationParser:
    """
    Uses Cohere RAG to parse user text and extract location keywords from their personal database
    """
    
    def __init__(self):
        self.cohere_client = co
    
    def parse_user_text_for_keywords(
        self, 
        user_text: str, 
        auth0_user_id: str,
        context_location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Parse user text using direct keyword matching (fallback when Cohere API unavailable)
        
        Args:
            user_text: The text input from user (voice or typed)
            auth0_user_id: User's Auth0 ID to access their keyword database
            context_location: Optional current location context {"lat": x, "lng": y}
            
        Returns:
            Dict containing:
            - matched_keywords: List of keywords found in user's database
            - location_data: Corresponding location data for matched keywords
            - confidence_scores: Confidence scores for each match
            - parsed_intent: Overall intent parsing result
        """
        try:
            # Get user's keyword database
            user_keywords = get_user_keywords(auth0_user_id)
            
            if not user_keywords:
                return {
                    "matched_keywords": [],
                    "location_data": [],
                    "confidence_scores": [],
                    "parsed_intent": {"message": "No keywords found in user database"},
                    "error": "User has no keywords in database"
                }
            
            # Use direct keyword matching (simpler and more reliable)
            matched_data = self._direct_keyword_matching(user_text, user_keywords)
            
            return {
                "matched_keywords": matched_data["keywords"],
                "location_data": matched_data["locations"],
                "confidence_scores": matched_data["confidence_scores"],
                "parsed_intent": {
                    "reasoning": f"Direct matching found {len(matched_data['keywords'])} keywords",
                    "intent": "location_search",
                    "context": "direct_matching"
                },
                "user_keywords_count": len(user_keywords)
            }
            
        except Exception as e:
            print(f"[Cohere RAG] Error parsing user text: {str(e)}")
            return {
                "matched_keywords": [],
                "location_data": [],
                "confidence_scores": [],
                "parsed_intent": {"error": str(e)},
                "error": str(e)
            }
    
    def _direct_keyword_matching(self, user_text: str, user_keywords: Dict[str, Any]) -> Dict[str, List]:
        """
        Direct keyword matching without API calls - simple and reliable
        """
        user_text_lower = user_text.lower()
        matched_keywords = []
        matched_locations = []
        confidence_scores = []
        
        # Direct keyword matching
        for keyword, location_data in user_keywords.items():
            keyword_lower = keyword.lower()
            
            # Check for exact keyword match
            if keyword_lower in user_text_lower:
                matched_keywords.append(keyword)
                matched_locations.append({
                    "keyword": keyword,
                    "location_data": location_data,
                    "confidence": 0.9  # High confidence for exact matches
                })
                confidence_scores.append(0.9)
                print(f"[Direct Matching] Found exact match: '{keyword}' in '{user_text}'")
            
            # Check for synonyms and variations
            elif self._check_synonyms(keyword_lower, user_text_lower):
                matched_keywords.append(keyword)
                matched_locations.append({
                    "keyword": keyword,
                    "location_data": location_data,
                    "confidence": 0.7  # Lower confidence for synonyms
                })
                confidence_scores.append(0.7)
                print(f"[Direct Matching] Found synonym match: '{keyword}' in '{user_text}'")
        
        return {
            "keywords": matched_keywords,
            "locations": matched_locations,
            "confidence_scores": confidence_scores
        }
    
    def _check_synonyms(self, keyword: str, text: str) -> bool:
        """
        Check for common synonyms and variations
        """
        synonym_map = {
            "coffee": ["coffee", "cafe", "café", "coffee shop", "coffeehouse"],
            "work": ["work", "office", "workplace", "job", "company"],
            "gym": ["gym", "fitness", "workout", "exercise", "fitness center"],
            "home": ["home", "house", "apartment", "place", "my place"],
            "restaurant": ["restaurant", "dining", "food", "eat", "meal"],
            "park": ["park", "green space", "outdoor", "nature"],
            "museum": ["museum", "gallery", "art", "exhibition"],
            "bar": ["bar", "pub", "drinks", "nightlife", "cocktail"]
        }
        
        synonyms = synonym_map.get(keyword, [keyword])
        return any(synonym in text for synonym in synonyms)

    def _create_knowledge_base(self, user_keywords: Dict[str, Any]) -> str:
        """
        Create a knowledge base string from user's keywords for RAG context
        """
        knowledge_entries = []
        
        for keyword, location_data in user_keywords.items():
            entry = f"""
Keyword: "{keyword}"
Location Name: {location_data.get('name', 'Unknown')}
Address: {location_data.get('address', 'Unknown')}
Coordinates: {location_data.get('lat', 'N/A')}, {location_data.get('lng', 'N/A')}
Place ID: {location_data.get('place_id', 'N/A')}
Added: {location_data.get('added_at', 'Unknown')}
---
"""
            knowledge_entries.append(entry)
        
        return "\n".join(knowledge_entries)
    
    def _cohere_rag_parse(
        self, 
        user_text: str, 
        knowledge_base: str,
        context_location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Use Cohere RAG to parse user text and find relevant keywords from knowledge base
        """
        try:
            # Build context-aware prompt
            context_info = ""
            if context_location:
                context_info = f"\nUser's current location: {context_location['lat']}, {context_location['lng']}"
            
            prompt = f"""
You are a location keyword parser for a travel app. Your job is to analyze user text and identify which keywords from their personal location database match what they're talking about.

USER TEXT: "{user_text}"
{context_info}

USER'S LOCATION KEYWORDS DATABASE:
{knowledge_base}

Analyze the user text and return a JSON response with:
1. "matched_keywords": Array of keyword strings that the user is referring to (IN ORDER OF MENTION)
2. "confidence_scores": Array of confidence scores (0.0-1.0) for each matched keyword
3. "reasoning": Brief explanation of why these keywords were matched
4. "intent": What the user seems to want to do (visit, find, go to, etc.)
5. "context": Any additional context about their request
6. "order_preserved": Boolean indicating if the order of locations was preserved
7. "wants_alternatives": Boolean indicating if user wants different options (e.g., "feeling like a different place today")

IMPORTANT RULES:
- PRESERVE ORDER: If user mentions locations in sequence, maintain that order in matched_keywords
- KEYWORD PRIORITY: If a personal keyword is matched, assume user wants THAT specific location unless they explicitly ask for alternatives
- ORDER INDICATORS: Look for words like "then", "after", "before", "first", "next" to determine sequence
- ALTERNATIVE REQUESTS: Only flag wants_alternatives=true if user explicitly asks for different options

Guidelines:
- Look for DIRECT matches between user text and the keywords in the database
- If user says "coffee" and there's a "coffee" keyword in the database, match it
- If user says "work" and there's a "work" keyword in the database, match it
- Consider synonyms: "gym" matches "gym", "fitness" could match "gym"
- Higher confidence (0.8-1.0) for exact matches, lower (0.5-0.7) for synonyms
- If no keywords match, return empty arrays
- Be liberal with matching - if it's reasonable, include it

Examples:
- "I want coffee" + keyword "coffee" → match with confidence 0.9, order_preserved=true, wants_alternatives=false
- "I go to work then buy chicken" + keywords ["work", "chicken"] → ["work", "chicken"], order_preserved=true
- "I go to work but first I will get chicken" + keywords ["work", "chicken"] → ["chicken", "work"], order_preserved=true
- "I'm feeling like a different coffee place today" + keyword "coffee" → ["coffee"], wants_alternatives=true

Return ONLY valid JSON, no other text.
"""
            
            response = self.cohere_client.chat(
                model="command-r-plus",
                message=prompt,
                temperature=0.1  # Low temperature for consistent parsing
            )
            
            # Parse the JSON response
            result = json.loads(response.text)
            print(f"[Cohere RAG] Raw response: {response.text}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"[Cohere RAG] JSON parsing error: {str(e)}")
            return {
                "matched_keywords": [],
                "confidence_scores": [],
                "reasoning": "JSON parsing failed",
                "intent": "unknown",
                "context": "parsing_error"
            }
        except Exception as e:
            print(f"[Cohere RAG] Cohere API error: {str(e)}")
            return {
                "matched_keywords": [],
                "confidence_scores": [],
                "reasoning": f"API error: {str(e)}",
                "intent": "unknown",
                "context": "api_error"
            }
    
    def _extract_matched_locations(
        self, 
        rag_result: Dict[str, Any], 
        user_keywords: Dict[str, Any]
    ) -> Dict[str, List]:
        """
        Extract location data for matched keywords
        """
        matched_keywords = rag_result.get("matched_keywords", [])
        confidence_scores = rag_result.get("confidence_scores", [])
        
        matched_locations = []
        valid_keywords = []
        valid_scores = []
        
        for i, keyword in enumerate(matched_keywords):
            if keyword in user_keywords:
                location_data = user_keywords[keyword]
                matched_locations.append({
                    "keyword": keyword,
                    "location_data": location_data,
                    "confidence": confidence_scores[i] if i < len(confidence_scores) else 0.5
                })
                valid_keywords.append(keyword)
                valid_scores.append(confidence_scores[i] if i < len(confidence_scores) else 0.5)
            else:
                print(f"[Cohere RAG] Warning: Keyword '{keyword}' not found in user database")
        
        return {
            "keywords": valid_keywords,
            "locations": matched_locations,
            "confidence_scores": valid_scores
        }
    
    def get_user_keyword_stats(self, auth0_user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's keyword database
        """
        try:
            user_keywords = get_user_keywords(auth0_user_id)
            
            if not user_keywords:
                return {
                    "total_keywords": 0,
                    "keyword_list": [],
                    "location_types": {},
                    "recent_additions": []
                }
            
            # Analyze keyword types
            location_types = {}
            recent_additions = []
            
            for keyword, data in user_keywords.items():
                # Categorize by location type (simple heuristic)
                name = data.get('name', '').lower()
                if any(word in name for word in ['restaurant', 'cafe', 'food', 'eat']):
                    location_types['food'] = location_types.get('food', 0) + 1
                elif any(word in name for word in ['park', 'garden', 'outdoor']):
                    location_types['outdoor'] = location_types.get('outdoor', 0) + 1
                elif any(word in name for word in ['museum', 'gallery', 'art']):
                    location_types['culture'] = location_types.get('culture', 0) + 1
                else:
                    location_types['other'] = location_types.get('other', 0) + 1
                
                # Track recent additions
                added_at = data.get('added_at')
                if added_at:
                    recent_additions.append({
                        'keyword': keyword,
                        'name': data.get('name'),
                        'added_at': added_at
                    })
            
            # Sort recent additions by date
            recent_additions.sort(key=lambda x: x['added_at'], reverse=True)
            
            return {
                "total_keywords": len(user_keywords),
                "keyword_list": list(user_keywords.keys()),
                "location_types": location_types,
                "recent_additions": recent_additions[:5]  # Top 5 most recent
            }
            
        except Exception as e:
            print(f"[Cohere RAG] Error getting user stats: {str(e)}")
            return {
                "total_keywords": 0,
                "keyword_list": [],
                "location_types": {},
                "recent_additions": [],
                "error": str(e)
            }


# Convenience functions for easy integration
def parse_user_text_with_rag(
    user_text: str, 
    auth0_user_id: str,
    context_location: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Convenience function to parse user text using Cohere RAG
    """
    parser = CohereRAGLocationParser()
    return parser.parse_user_text_for_keywords(user_text, auth0_user_id, context_location)

def get_user_location_keywords_stats(auth0_user_id: str) -> Dict[str, Any]:
    """
    Convenience function to get user keyword statistics
    """
    parser = CohereRAGLocationParser()
    return parser.get_user_keyword_stats(auth0_user_id)
