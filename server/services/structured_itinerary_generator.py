"""
Structured itinerary generator following specific rules for sidequests
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from services.user_profile_service import filter_unvisited_activities, get_or_create_user_profile
from schemas.sidequest import INTEREST_CATEGORIES
import json

def generate_structured_itinerary(
    activities: List[Dict[str, Any]],
    start_time: str,
    end_time: str,
    interests: List[str],
    user_id: str = None,
    budget: float = None,
    energy: int = 5,
    indoor_outdoor: str = None
) -> Dict[str, Any]:
    """
    Generate structured itinerary following specific rules:
    1. One location per interest category
    2. Max 3 meals/day, 2 meals/half day
    3. At least one unvisited place
    4. Prioritize meals + entertainment over meals + bites when time is short
    5. Spread food throughout the day
    """
    print(f"[Structured Itinerary] Generating itinerary from {start_time} to {end_time}")
    print(f"[Structured Itinerary] Interests: {interests}")
    
    # Calculate available time
    start_dt = datetime.strptime(start_time, "%H:%M")
    end_dt = datetime.strptime(end_time, "%H:%M")
    available_hours = (end_dt - start_dt).total_seconds() / 3600
    
    print(f"[Structured Itinerary] Available time: {available_hours} hours")
    
    if not activities:
        return _create_empty_itinerary()
    
    # Filter out visited places
    unvisited_activities = filter_unvisited_activities(activities, user_id)
    
    if not unvisited_activities:
        print("[Structured Itinerary] All activities have been visited, using all activities")
        unvisited_activities = activities
    
    # Validate interests
    valid_interests = [interest for interest in interests if interest in INTEREST_CATEGORIES]
    if not valid_interests:
        print("[Structured Itinerary] No valid interests, using default: entertainment")
        valid_interests = ["entertainment"]
    
    # Apply structured selection rules
    selected_activities = _apply_structured_rules(
        unvisited_activities, 
        valid_interests, 
        available_hours,
        budget,
        energy,
        indoor_outdoor
    )
    
    # Order activities logically with time slots
    ordered_activities = _assign_time_slots(selected_activities, start_time, end_time)
    
    # Calculate totals (use unwrapped activities for calculations)
    unwrapped_for_calc = []
    for activity in ordered_activities:
        if "structured" in activity:
            unwrapped_for_calc.append(activity["structured"])
        else:
            unwrapped_for_calc.append(activity)
    
    total_duration = sum(activity.get("duration_hours", 0) for activity in unwrapped_for_calc)
    total_cost = sum(activity.get("cost", 0) for activity in unwrapped_for_calc)
    
    # Generate summary (use unwrapped activities for summary)
    unwrapped_for_summary = []
    for activity in ordered_activities:
        if "structured" in activity:
            unwrapped_for_summary.append(activity["structured"])
        else:
            unwrapped_for_summary.append(activity)
    summary = _generate_structured_summary(unwrapped_for_summary, valid_interests, available_hours)
    
    # Unwrap activities for API response format
    unwrapped_activities = []
    for activity in ordered_activities:
        if "structured" in activity:
            # Extract the structured data and add any additional fields
            unwrapped_activity = activity["structured"].copy()
            # Add any additional metadata if needed
            unwrapped_activities.append(unwrapped_activity)
        else:
            # Already unwrapped
            unwrapped_activities.append(activity)
    
    return {
        "itinerary": unwrapped_activities,
        "total_duration": total_duration,
        "total_cost": total_cost,
        "summary": summary,
        "metadata": {
            "activities_considered": len(activities),
            "activities_selected": len(selected_activities),
            "activities_in_itinerary": len(unwrapped_activities),
            "interests_covered": valid_interests,
            "unvisited_places": len([a for a in unwrapped_activities if a.get("is_new_place", True)])
        }
    }

def _apply_structured_rules(
    activities: List[Dict[str, Any]], 
    interests: List[str], 
    available_hours: float,
    budget: float = None,
    energy: int = 5,
    indoor_outdoor: str = None
) -> List[Dict[str, Any]]:
    """
    Apply structured rules to select activities with better time distribution
    """
    selected = []
    covered_interests = set()
    
    # Rule 1: Select ONE activity per interest (no duplicates)
    used_activities = set()  # Track used activities to prevent duplicates
    
    for interest in interests:
        interest_activities = _find_activities_for_interest(activities, interest, budget, energy, indoor_outdoor)
        
        # Select the FIRST available activity for this interest (no duplicates)
        selected_activity = None
        for activity in interest_activities:
            activity_id = activity.get("structured", {}).get("place_id", activity.get("structured", {}).get("title", ""))
            if activity_id not in used_activities:
                selected_activity = activity
                used_activities.add(activity_id)
                break
        
        if selected_activity:
            selected.append(selected_activity)
            covered_interests.add(interest)
            print(f"[Structured Rules] Selected {interest}: {selected_activity.get('structured', {}).get('title', 'Unknown')}")
        else:
            # Fallback: if no exact match, pick any unused activity
            print(f"[Structured Rules] No exact match for {interest}, using fallback")
            for activity in activities:
                activity_id = activity.get("structured", {}).get("place_id", activity.get("structured", {}).get("title", ""))
                if activity_id not in used_activities:
                    selected.append(activity)
                    used_activities.add(activity_id)
                    covered_interests.add(interest)
                    print(f"[Structured Rules] Fallback selected {interest}: {activity.get('structured', {}).get('title', 'Unknown')}")
                    break
    
    # Rule 2: Apply meal limits
    selected = _apply_meal_limits(selected, available_hours)
    
    # Rule 3: Ensure at least one unvisited place (already handled by filter_unvisited_activities)
    
    # Rule 4: If time is short, prioritize meals + entertainment over meals + bites
    if available_hours < 4:  # Short time
        selected = _prioritize_for_short_time(selected, interests)
    
    # Rule 5: Spread food throughout the day
    selected = _spread_food_throughout_day(selected, available_hours)
    
    print(f"[Structured Rules] Selected {len(selected)} activities covering {covered_interests}")
    return selected

def _find_activities_for_interest(
    activities: List[Dict[str, Any]], 
    interest: str, 
    budget: float = None,
    energy: int = 5,
    indoor_outdoor: str = None
) -> List[Dict[str, Any]]:
    """
    Find all activities for a specific interest category, sorted by quality
    """
    # Use flexible matching instead of rigid mappings
    matching_activities = []
    print(f"[Structured Rules] Looking for {interest} activities using flexible matching")
    
    # Simple flexible mapping for better matching
    flexible_mapping = {
        "meals": ["meals", "food", "restaurant", "meal"],
        "bites": ["bites", "cafe", "snack", "bakery"],
        "entertainment": ["entertainment", "movie", "theater", "cinema", "show", "club", "bar"],
        "events": ["events", "festival", "concert", "amusement"],
        "scenery": ["scenery", "park", "landmark", "viewpoint", "garden"],
        "culture": ["culture", "museum", "gallery", "library", "cultural"],
        "shopping": ["shopping", "store", "mall", "market"],
        "physical_activity": ["physical", "gym", "sports", "fitness", "stadium"]
    }
    
    target_types = flexible_mapping.get(interest, [interest])
    
    for activity in activities:
        activity_type = activity.get("structured", {}).get("activity_type", "general")
        title = activity.get("structured", {}).get("title", "Unknown")
        
        # Check if activity matches the interest
        matches = False
        
        # Direct type match
        if activity_type in target_types:
            matches = True
        
        # Title contains interest keywords
        elif any(keyword in title.lower() for keyword in target_types):
            matches = True
        
        # Only add if it actually matches
        if matches:
            matching_activities.append(activity)
            print(f"[Structured Rules] Matched {interest} activity: {title} (type: {activity_type})")
    
    print(f"[Structured Rules] Found {len(matching_activities)} activities for {interest}")
    return matching_activities

async def _llm_matches_interest(title: str, description: str, activity_type: str, interest: str) -> bool:
    """
    Use LLM to determine if an activity matches an interest category
    """
    try:
        # Import Cohere client
        import cohere
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        co = cohere.Client(os.getenv("COHERE_API_KEY"))
        
        prompt = f"""
        Determine if this activity matches the interest category "{interest}".

        Activity: {title}
        Description: {description}
        Current Type: {activity_type}
        
        Interest Categories:
        - meals: restaurants, food places, dining
        - bites: cafes, snacks, quick food, bakeries
        - entertainment: movies, parties, concerts, clubs, shows, nightlife
        - events: special events, festivals, concerts, shows
        - scenery: parks, landmarks, natural attractions, viewpoints
        - culture: art galleries, museums, cultural sites, libraries
        - shopping: stores, malls, markets, retail
        - physical_activity: gyms, sports, fitness, outdoor activities
        
        Answer with just "YES" or "NO":
        """
        
        # Add timeout to prevent hanging
        import asyncio
        response = await asyncio.wait_for(
            co.chat(model="command-r-plus", message=prompt),
            timeout=3.0  # 3 second timeout
        )
        result = response.text.strip().upper()
        
        return result == "YES"
        
    except Exception as e:
        print(f"[LLM Matching] Error: {e}, falling back to simple matching")
        # Fallback to simple matching
        return activity_type == interest or interest in title.lower()

def _calculate_max_activities_for_interest(interest: str, available_hours: float, num_interests: int) -> int:
    """
    Calculate how many activities we can fit for a specific interest
    """
    # Base duration per activity (max 2 hours unless it's a specific event)
    base_duration = 2.0  # Max 2 hours per activity
    
    # Special cases for events that have fixed durations
    if interest in ["entertainment", "events"]:
        base_duration = 2.5  # Movies, shows, etc. might be longer
    
    # Calculate how many activities we can fit
    # Reserve some time for travel between activities (15 min = 0.25 hours)
    travel_time_per_activity = 0.25
    
    # Available time per interest
    time_per_interest = available_hours / num_interests
    
    # Calculate max activities: (time_per_interest) / (base_duration + travel_time)
    max_activities = int(time_per_interest / (base_duration + travel_time_per_activity))
    
    # Ensure minimum of 1 and maximum of 3 activities per interest
    max_activities = max(1, min(max_activities, 3))
    
    print(f"[Structured Rules] Interest {interest}: can fit {max_activities} activities in {time_per_interest:.1f} hours")
    return max_activities

def _find_best_activity_for_interest(
    activities: List[Dict[str, Any]], 
    interest: str, 
    budget: float = None,
    energy: int = 5,
    indoor_outdoor: str = None
) -> Optional[Dict[str, Any]]:
    """
    Find the best activity for a specific interest category
    """
    # Map interest categories to activity types - be more inclusive
    interest_mapping = {
        "shopping": ["shopping", "general"],
        "meals": ["meals", "food", "restaurant"],  # Include all possible types
        "bites": ["bites", "food", "cafe"],
        "entertainment": ["entertainment", "cultural", "amusement_park"],
        "events": ["events", "entertainment"],
        "culture": ["culture", "cultural", "museum"],
        "physical_activity": ["physical_activity", "physical", "scenery", "gym"],
        "scenery": ["scenery", "physical", "park"]
    }
    
    target_types = interest_mapping.get(interest, ["general"])
    
    # Find the first activity that matches the interest type - simplified approach
    print(f"[Structured Rules] Looking for interest: {interest}, target_types: {target_types}")
    
    for activity in activities:
        activity_type = activity.get("structured", {}).get("activity_type", "general")
        title = activity.get("structured", {}).get("title", "Unknown")
        print(f"[Structured Rules] Checking activity: {title} with type: {activity_type}")
        
        # Direct match or fallback to any activity if no exact match
        if activity_type in target_types or activity_type == interest:
            print(f"[Structured Rules] Selected {interest}: {title}")
            return activity
    
    # If no exact match, just return the first activity for this interest
    print(f"[Structured Rules] No exact match found, returning first activity for {interest}")
    if activities:
        first_activity = activities[0]
        print(f"[Structured Rules] Selected {interest}: {first_activity.get('structured', {}).get('title', 'Unknown')}")
        return first_activity
    
    print(f"[Structured Rules] No activities found for interest: {interest}")
    return None

def _apply_meal_limits(activities: List[Dict[str, Any]], available_hours: float) -> List[Dict[str, Any]]:
    """
    Apply meal limits: max 3 meals/day, 2 meals/half day
    """
    meal_activities = [a for a in activities if a.get("structured", {}).get("activity_type") == "food"]
    
    if available_hours >= 8:  # Full day
        max_meals = 3
    else:  # Half day
        max_meals = 2
    
    if len(meal_activities) > max_meals:
        # Keep the best meals (highest confidence)
        meal_activities.sort(key=lambda x: x.get("structured", {}).get("confidence", 0), reverse=True)
        meal_activities = meal_activities[:max_meals]
        
        # Remove excess meals from activities list
        non_meal_activities = [a for a in activities if a.get("structured", {}).get("activity_type") != "food"]
        activities = non_meal_activities + meal_activities
        
        print(f"[Meal Limits] Limited to {max_meals} meals for {available_hours}h day")
    
    return activities

def _prioritize_for_short_time(activities: List[Dict[str, Any]], interests: List[str]) -> List[Dict[str, Any]]:
    """
    For short time, prioritize meals + entertainment over meals + bites
    """
    if len(activities) <= 2:
        return activities
    
    # If we have both meals and bites, prefer meals + entertainment
    has_meals = any("meals" in interests)
    has_bites = any("bites" in interests)
    has_entertainment = any("entertainment" in interests)
    
    if has_meals and has_bites and has_entertainment:
        # Remove bites, keep meals + entertainment
        activities = [a for a in activities if a.get("structured", {}).get("activity_type") != "food" or 
                     a.get("structured", {}).get("title", "").lower() not in ["cafe", "coffee", "snack"]]
        print("[Short Time Priority] Prioritized meals + entertainment over bites")
    
    return activities

def _spread_food_throughout_day(activities: List[Dict[str, Any]], available_hours: float) -> List[Dict[str, Any]]:
    """
    Spread food activities throughout the day
    """
    food_activities = [a for a in activities if a.get("structured", {}).get("activity_type") == "food"]
    
    if len(food_activities) > 1 and available_hours > 4:
        # Add timing hints for food activities
        for i, activity in enumerate(food_activities):
            if i == 0:
                activity["meal_type"] = "breakfast"
            elif i == 1:
                activity["meal_type"] = "lunch"
            elif i == 2:
                activity["meal_type"] = "dinner"
        
        print("[Food Spreading] Added meal timing hints")
    
    return activities

def _assign_time_slots(activities: List[Dict[str, Any]], start_time: str, end_time: str) -> List[Dict[str, Any]]:
    """
    Assign specific time slots to activities
    """
    start_dt = datetime.strptime(start_time, "%H:%M")
    current_time = start_dt
    
    for activity in activities:
        # Handle both wrapped and unwrapped activity structures
        if "structured" in activity:
            activity_data = activity["structured"]
        else:
            activity_data = activity
            
        duration_hours = activity_data.get("duration_hours", 1.5)
        
        # Assign start time
        activity_data["start_time"] = current_time.strftime("%H:%M")
        
        # Move to next time slot
        current_time += timedelta(hours=duration_hours)
        
        # Add travel time between activities (15 minutes)
        current_time += timedelta(minutes=15)
    
    return activities

def _generate_structured_summary(activities: List[Dict[str, Any]], interests: List[str], available_hours: float) -> str:
    """
    Generate a clear and informative summary explaining the structured itinerary
    """
    if not activities:
        return "No activities could be selected based on your preferences and constraints."
    
    # Analyze actual activity types in the itinerary
    activity_types = []
    for activity in activities:
        activity_type = activity.get("activity_type", "unknown")
        activity_types.append(activity_type)
    
    # Count activities by type
    type_counts = {}
    for activity_type in activity_types:
        type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
    
    # Determine which interests were covered
    covered_interests = []
    missed_interests = []
    
    for interest in interests:
        # Check if any activity matches this interest
        interest_matched = False
        for activity in activities:
            activity_type = activity.get("activity_type", "")
            title = activity.get("title", "").lower()
            
            # Flexible matching for interests
            if interest == "meals" and activity_type == "meals":
                interest_matched = True
            elif interest == "bites" and activity_type == "bites":
                interest_matched = True
            elif interest == "entertainment" and activity_type == "entertainment":
                interest_matched = True
            elif interest == "scenery" and activity_type == "scenery":
                interest_matched = True
            elif interest == "culture" and activity_type == "culture":
                interest_matched = True
            elif interest == "shopping" and activity_type == "shopping":
                interest_matched = True
            elif interest == "physical_activity" and activity_type == "physical_activity":
                interest_matched = True
            elif interest == "events" and activity_type == "events":
                interest_matched = True
        
        if interest_matched:
            covered_interests.append(interest)
        else:
            missed_interests.append(interest)
    
    # Build comprehensive summary
    summary_parts = []
    
    # Main coverage statement
    if covered_interests:
        summary_parts.append(f"Your {available_hours}-hour sidequest includes {len(activities)} activities covering: {', '.join(covered_interests)}")
    else:
        summary_parts.append(f"Your {available_hours}-hour sidequest includes {len(activities)} activities")
    
    # Explain what each activity is
    activity_descriptions = []
    for activity in activities:
        activity_type = activity.get("activity_type", "activity")
        title = activity.get("title", "Unknown")
        activity_descriptions.append(f"{activity_type}: {title}")
    
    if activity_descriptions:
        summary_parts.append(f"Activities: {'; '.join(activity_descriptions)}")
    
    # Explain missed interests
    if missed_interests:
        summary_parts.append(f"Note: Could not find suitable activities for: {', '.join(missed_interests)}")
    
    # Add practical information
    total_cost = sum(activity.get("cost", 0) for activity in activities)
    if total_cost > 0:
        summary_parts.append(f"Total estimated cost: ${total_cost}")
    
    new_places = len([a for a in activities if a.get("is_new_place", True)])
    if new_places > 0:
        summary_parts.append(f"You'll discover {new_places} new place{'s' if new_places > 1 else ''} you haven't visited before")
    
    return ". ".join(summary_parts) + "."

def _get_activity_types_for_interest(interest: str) -> List[str]:
    """Get activity types that fulfill an interest"""
    mapping = {
        "shopping": ["shopping", "general"],
        "meals": ["food"],
        "bites": ["food"],
        "entertainment": ["entertainment", "cultural"],
        "physical_activity": ["physical", "scenery"],
        "scenery": ["scenery", "physical"]
    }
    return mapping.get(interest, ["general"])

def _create_empty_itinerary() -> Dict[str, Any]:
    """Create empty itinerary response"""
    return {
        "itinerary": [],
        "total_duration": 0,
        "total_cost": 0,
        "summary": "No activities available",
        "metadata": {
            "activities_considered": 0,
            "activities_selected": 0,
            "activities_in_itinerary": 0,
            "interests_covered": [],
            "unvisited_places": 0
        }
    }
