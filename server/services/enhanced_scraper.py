"""
Fast trendiness checker using Cohere for top activity candidates only
"""
import os
import json
import requests
from dotenv import load_dotenv
import cohere
from typing import Dict, Any
import hashlib
from datetime import datetime, timedelta

load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

class EnhancedScraper:
    def __init__(self):
        self.cohere_client = co
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # In-memory cache (could be moved to MongoDB later)
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
    
    async def check_trendiness(self, place_name: str, location: str) -> float:
        """
        Fast trendiness check using Cohere for top candidates only.
        Returns trendiness score (0-1, higher = more trendy).
        """
        # Check cache first
        cache_key = self._get_cache_key(place_name, location)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            print(f"[Trendiness] Cache HIT for: {place_name}")
            return cached_result
        
        print(f"[Trendiness] Cache MISS - checking: {place_name}")
        
        try:
            trendiness_score = await self._analyze_trendiness(place_name, location)
            
            # Cache the result
            self._save_to_cache(cache_key, trendiness_score)
            
            return trendiness_score
            
        except Exception as e:
            print(f"[Trendiness] Error checking {place_name}: {e}")
            fallback_score = 0.5  # Neutral trendiness
            self._save_to_cache(cache_key, fallback_score)
            return fallback_score
    
    async def _analyze_trendiness(self, place_name: str, location: str) -> float:
        """Analyze trendiness using Cohere - focused on social media/blog presence"""
        try:
            prompt = f"""
            Rate the trendiness/popularity of this place on a scale of 0.0 to 1.0:
            
            Place: {place_name}
            Location: {location}
            
            Consider:
            - Social media mentions
            - Blog posts about this place
            - Recent reviews and buzz
            - Instagram-worthy factor
            - Local popularity vs tourist traps
            
            Return ONLY a number between 0.0 and 1.0 (no explanation):
            - 0.0-0.3: Not trendy, local only
            - 0.3-0.6: Moderately popular
            - 0.6-0.8: Trending, getting attention
            - 0.8-1.0: Very trendy, viral/hot spot
            """
            
            response = co.chat(model="command-r-plus", message=prompt)
            
            # Extract number from response
            cleaned_text = response.text.strip()
            try:
                # Try to find a number in the response
                import re
                numbers = re.findall(r'0\.\d+', cleaned_text)
                if numbers:
                    trendiness = float(numbers[0])
                    print(f"[Trendiness] {place_name}: {trendiness}")
                    return trendiness
                else:
                    # Fallback: try to parse the whole response as a number
                    trendiness = float(cleaned_text)
                    return max(0.0, min(1.0, trendiness))  # Clamp to 0-1
            except ValueError:
                print(f"[Trendiness] Could not parse response: {cleaned_text}")
                return 0.5  # Neutral fallback
                
        except Exception as e:
            print(f"[Trendiness] Error analyzing {place_name}: {e}")
            return 0.5  # Neutral fallback
    
    
    def _get_cache_key(self, place_name: str, location: str) -> str:
        """Generate cache key from place name and location"""
        key_string = f"{place_name.lower().strip()}_{location.lower().strip()}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Dict[str, Any]:
        """Get cached result if still valid"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = cached_data.get("cached_at")
            if cache_time and datetime.now() - cache_time < self.cache_duration:
                return cached_data.get("data")
            else:
                # Expired cache entry
                del self.cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Save result to cache with timestamp"""
        self.cache[cache_key] = {
            "data": data,
            "cached_at": datetime.now()
        }
        print(f"[Enhanced Scraper] Cached result for key: {cache_key[:8]}...")

# Global instance
trendiness_checker = EnhancedScraper()