"""
Luma and blog scraping service for real activity data with Cohere interpretation
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import cohere

load_dotenv()

# Initialize Cohere client
co = cohere.Client(os.getenv("COHERE_API_KEY"))

def fetch_luma_events(city: str, lat: float = None, lon: float = None) -> List[Dict[str, Any]]:
    """
    Scrape events from Luma (luma.com) for a given city
    """
    print(f"[Luma] Fetching events for {city}")
    
    events = []
    
    try:
        # Luma search URL - they have a public events page
        search_url = f"https://lu.ma/search?q={city}&type=event"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for event cards or listings
        event_elements = soup.find_all(['div', 'article'], class_=re.compile(r'event|card|listing'))
        
        for element in event_elements[:10]:  # Limit to 10 events
            try:
                event_data = _extract_luma_event_data(element, city)
                if event_data:
                    events.append(event_data)
            except Exception as e:
                print(f"[Luma] Error extracting event: {e}")
                continue
                
    except Exception as e:
        print(f"[Luma] Error fetching from Luma: {e}")
    
    print(f"[Luma] Found {len(events)} events")
    return events

def _extract_luma_event_data(element, city: str) -> Dict[str, Any]:
    """Extract event data from a Luma HTML element using Cohere for interpretation"""
    try:
        # Extract raw text data
        title_elem = element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name|event'))
        title = title_elem.get_text(strip=True) if title_elem else "Luma Event"
        
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time'))
        date_text = date_elem.get_text(strip=True) if date_elem else None
        
        location_elem = element.find(['span', 'div'], class_=re.compile(r'location|venue|place'))
        location = location_elem.get_text(strip=True) if location_elem else city
        
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary'))
        description = desc_elem.get_text(strip=True) if desc_elem else ""
        
        price_elem = element.find(['span', 'div'], class_=re.compile(r'price|cost|ticket'))
        price_text = price_elem.get_text(strip=True) if price_elem else "Free"
        
        # Combine all text for Cohere analysis
        full_text = f"Title: {title}\nDate: {date_text}\nLocation: {location}\nDescription: {description}\nPrice: {price_text}"
        
        # Use Cohere to interpret the event data
        structured = _interpret_event_with_cohere(full_text, city)
        
        print(f"[Luma] Cohere interpreted: {title} -> {structured.get('activity_type', 'unknown')} (${structured.get('cost', 0)})")
        
        return {
            "raw_name": title,
            "place_id": f"luma_{hash(title)}",
            "structured": structured
        }
        
    except Exception as e:
        print(f"[Luma] Error extracting event data: {e}")
        return None

def _interpret_event_with_cohere(event_text: str, city: str) -> Dict[str, Any]:
    """Use Cohere to interpret event data and extract structured information"""
    try:
        prompt = f"""
        Analyze this event data and extract structured information:
        
        {event_text}
        
        City: {city}
        
        Return a JSON object with these fields:
        {{
            "title": "event title",
            "location": "full location",
            "start_time": "date/time string or null",
            "duration_hours": "realistic duration in hours",
            "cost": "realistic cost per person (number)",
            "activity_type": "food/scenery/physical/cultural/shopping/entertainment",
            "indoor_outdoor": "indoor/outdoor/mixed",
            "energy_level": "1-10 scale",
            "confidence": "0.0-1.0",
            "description": "brief description",
            "highlights": "key features"
        }}
        
        Guidelines:
        - Cost should be realistic and varied (not all the same)
        - Duration should be appropriate for the event type
        - Activity type should match the event content
        - Energy level should reflect the event intensity
        - Confidence should reflect data quality
        """
        
        response = co.chat(model="command-r-plus", message=prompt)
        
        # Handle empty or malformed responses
        if not response.text or response.text.strip() == "":
            print(f"[Luma] Empty response from Cohere")
            return {
                "title": "Luma Event",
                "location": city,
                "start_time": None,
                "duration_hours": 2.0,
                "cost": 0,
                "activity_type": "entertainment",
                "indoor_outdoor": "mixed",
                "energy_level": 5,
                "confidence": 0.3,
                "description": "Local event",
                "highlights": "Unknown"
            }
        
        try:
            structured_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"[Luma] JSON decode error: {e}")
            print(f"[Luma] Raw response: {response.text[:200]}...")
            return {
                "title": "Luma Event",
                "location": city,
                "start_time": None,
                "duration_hours": 2.0,
                "cost": 0,
                "activity_type": "entertainment",
                "indoor_outdoor": "mixed",
                "energy_level": 5,
                "confidence": 0.3,
                "description": "Local event",
                "highlights": "Unknown"
            }
        
        # Ensure required fields exist
        structured_data.setdefault("title", "Luma Event")
        structured_data.setdefault("location", city)
        structured_data.setdefault("start_time", None)
        structured_data.setdefault("duration_hours", 2.0)
        structured_data.setdefault("cost", 0)
        structured_data.setdefault("activity_type", "entertainment")
        structured_data.setdefault("indoor_outdoor", "mixed")
        structured_data.setdefault("energy_level", 5)
        structured_data.setdefault("confidence", 0.7)
        structured_data.setdefault("description", "")
        structured_data.setdefault("highlights", "")
        
        return structured_data
        
    except Exception as e:
        print(f"[Luma] Cohere interpretation error: {e}")
        # Fallback to basic extraction
        return {
            "title": "Luma Event",
            "location": city,
            "start_time": None,
            "duration_hours": 2.0,
            "cost": 0,
            "activity_type": "entertainment",
            "indoor_outdoor": "mixed",
            "energy_level": 5,
            "confidence": 0.3,
            "description": "Local event",
            "highlights": "Unknown"
        }

def fetch_local_blog_events(city: str, lat: float = None, lon: float = None) -> List[Dict[str, Any]]:
    """
    Scrape events from local blogs and event websites
    """
    print(f"[Blog Scraper] Fetching events for {city}")
    
    events = []
    
    # Common local event blog patterns
    blog_patterns = [
        f"{city.lower()}events.com",
        f"{city.lower()}blog.com",
        f"eventsin{city.lower()}.com",
        f"{city.lower()}happening.com"
    ]
    
    for pattern in blog_patterns:
        try:
            url = f"https://{pattern}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                events.extend(_scrape_blog_events(response.content, city))
                
        except Exception as e:
            print(f"[Blog Scraper] Could not fetch {pattern}: {e}")
            continue
    
    print(f"[Blog Scraper] Found {len(events)} events from blogs")
    return events

def _scrape_blog_events(content, city: str) -> List[Dict[str, Any]]:
    """Scrape events from blog content"""
    events = []
    
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for common event patterns
        event_selectors = [
            'article.event',
            'div.event-item',
            'li.event',
            '.event-listing',
            '[class*="event"]'
        ]
        
        for selector in event_selectors:
            elements = soup.select(selector)
            for element in elements[:5]:  # Limit per selector
                event_data = _extract_blog_event_data(element, city)
                if event_data:
                    events.append(event_data)
                    
    except Exception as e:
        print(f"[Blog Scraper] Error parsing blog content: {e}")
    
    return events

def _extract_blog_event_data(element, city: str) -> Dict[str, Any]:
    """Extract event data from blog HTML element using Cohere interpretation"""
    try:
        # Extract raw text data
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])
        title = title_elem.get_text(strip=True) if title_elem else "Local Event"
        
        date_elem = element.find(['time', 'span'], class_=re.compile(r'date|time'))
        date_text = date_elem.get_text(strip=True) if date_elem else None
        
        location_elem = element.find(['span', 'div'], class_=re.compile(r'location|venue'))
        location = location_elem.get_text(strip=True) if location_elem else city
        
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary'))
        description = desc_elem.get_text(strip=True) if desc_elem else ""
        
        # Combine all text for Cohere analysis
        full_text = f"Title: {title}\nDate: {date_text}\nLocation: {location}\nDescription: {description}"
        
        # Use Cohere to interpret the blog event data
        structured = _interpret_event_with_cohere(full_text, city)
        
        print(f"[Blog Scraper] Cohere interpreted: {title} -> {structured.get('activity_type', 'unknown')} (${structured.get('cost', 0)})")
        
        return {
            "raw_name": title,
            "place_id": f"blog_{hash(title)}",
            "structured": structured
        }
        
    except Exception as e:
        print(f"[Blog Scraper] Error extracting event data: {e}")
        return None

def _estimate_cost_from_text(price_text: str) -> float:
    """Estimate cost from price text"""
    if not price_text:
        return 0
    
    price_text = price_text.lower()
    
    if "free" in price_text or "$0" in price_text:
        return 0
    elif "donation" in price_text:
        return 10
    elif "$" in price_text:
        # Extract dollar amounts
        amounts = re.findall(r'\$(\d+)', price_text)
        if amounts:
            return float(amounts[0])
    
    return 15  # Default moderate cost

def _determine_activity_type_from_text(text: str) -> str:
    """Determine activity type from text content"""
    text = text.lower()
    
    if any(word in text for word in ["food", "restaurant", "dining", "eat", "meal", "cafe", "bar"]):
        return "food"
    elif any(word in text for word in ["park", "outdoor", "nature", "hiking", "walk", "scenic"]):
        return "scenery"
    elif any(word in text for word in ["museum", "art", "gallery", "culture", "history", "exhibition"]):
        return "cultural"
    elif any(word in text for word in ["music", "concert", "performance", "show", "entertainment"]):
        return "entertainment"
    elif any(word in text for word in ["sport", "fitness", "gym", "run", "bike", "physical"]):
        return "physical"
    elif any(word in text for word in ["shop", "market", "retail", "store"]):
        return "shopping"
    else:
        return "general"

def _determine_indoor_outdoor_from_text(text: str) -> str:
    """Determine indoor/outdoor from text content"""
    text = text.lower()
    
    outdoor_keywords = ["outdoor", "park", "street", "plaza", "square", "beach", "garden", "patio"]
    indoor_keywords = ["indoor", "venue", "hall", "theater", "museum", "restaurant", "cafe", "bar"]
    
    if any(keyword in text for keyword in outdoor_keywords):
        return "outdoor"
    elif any(keyword in text for keyword in indoor_keywords):
        return "indoor"
    else:
        return "indoor"  # Default to indoor

def _estimate_energy_level_from_text(text: str) -> int:
    """Estimate energy level from text content"""
    text = text.lower()
    
    if any(word in text for word in ["relax", "quiet", "meditation", "yoga", "low-key"]):
        return 2
    elif any(word in text for word in ["walk", "stroll", "easy", "gentle"]):
        return 4
    elif any(word in text for word in ["active", "sport", "fitness", "run", "bike"]):
        return 8
    elif any(word in text for word in ["party", "dance", "high-energy", "intense"]):
        return 9
    else:
        return 5  # Default moderate energy

def _calculate_scraped_confidence(title: str, date_text: str, location: str) -> float:
    """Calculate confidence score for scraped data"""
    confidence = 0.5  # Base confidence
    
    if title and len(title) > 5:
        confidence += 0.2
    
    if date_text:
        confidence += 0.1
    
    if location and location != "Unknown":
        confidence += 0.1
    
    return min(confidence, 1.0)
