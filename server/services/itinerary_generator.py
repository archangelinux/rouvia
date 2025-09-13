"""
Itinerary generation service to create coherent activity plans
"""
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

def generate_itinerary(
    activities: List[Dict[str, Any]], 
    available_time: float,
    start_time: str = None,
    preferences: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate a coherent itinerary from a list of activities
    
    Args:
        activities: List of structured activities
        available_time: Total time available in hours
        start_time: Optional start time (e.g., "14:00")
        preferences: User preferences for itinerary generation
        
    Returns:
        Dictionary containing the generated itinerary
    """
    print(f"[Itinerary] Generating itinerary from {len(activities)} activities")
    print(f"[Itinerary] Available time: {available_time} hours")
    
    if not activities:
        return {
            "itinerary": [],
            "total_duration": 0,
            "total_cost": 0,
            "summary": "No activities available"
        }
    
    # Sort activities by confidence and user preferences
    sorted_activities = _sort_activities_by_preference(activities, preferences)
    
    # Select activities that fit within available time
    selected_activities = _select_activities_for_time(sorted_activities, available_time)
    
    # Order activities logically (considering location, time, energy levels)
    ordered_activities = _order_activities_logically(selected_activities, start_time)
    
    # Calculate totals
    total_duration = sum(activity.get("duration_hours", 0) for activity in ordered_activities)
    total_cost = sum(activity.get("cost", 0) for activity in ordered_activities)
    
    # Generate summary
    summary = _generate_itinerary_summary(ordered_activities, total_duration, total_cost)
    
    itinerary = {
        "itinerary": ordered_activities,
        "total_duration": total_duration,
        "total_cost": total_cost,
        "summary": summary,
        "metadata": {
            "activities_considered": len(activities),
            "activities_selected": len(selected_activities),
            "activities_in_itinerary": len(ordered_activities),
            "generation_time": datetime.now().isoformat()
        }
    }
    
    print(f"[Itinerary] Generated itinerary with {len(ordered_activities)} activities")
    print(f"[Itinerary] Total duration: {total_duration}h, Total cost: ${total_cost}")
    
    return itinerary

def _sort_activities_by_preference(activities: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Sort activities based on user preferences and confidence scores"""
    if not preferences:
        return sorted(activities, key=lambda x: x.get("confidence", 0), reverse=True)
    
    def preference_score(activity):
        score = activity.get("confidence", 0)
        
        # Boost score for matching interests
        if preferences.get("interests"):
            activity_type = activity.get("activity_type", "").lower()
            for interest in preferences["interests"]:
                if interest.lower() in activity_type:
                    score += 0.2
        
        # Boost score for matching indoor/outdoor preference
        if preferences.get("indoor_outdoor"):
            if activity.get("indoor_outdoor", "").lower() == preferences["indoor_outdoor"].lower():
                score += 0.15
        
        # Boost score for budget-friendly activities
        if preferences.get("budget"):
            activity_cost = activity.get("cost", 0)
            if activity_cost <= preferences["budget"] * 0.5:  # Very budget-friendly
                score += 0.1
            elif activity_cost <= preferences["budget"]:  # Within budget
                score += 0.05
        
        # Boost score for energy level match
        if preferences.get("energy"):
            activity_energy = activity.get("energy_level", 5)
            energy_diff = abs(activity_energy - preferences["energy"])
            if energy_diff <= 1:  # Close match
                score += 0.1
            elif energy_diff <= 2:  # Reasonable match
                score += 0.05
        
        return score
    
    return sorted(activities, key=preference_score, reverse=True)

def _select_activities_for_time(activities: List[Dict[str, Any]], available_time: float) -> List[Dict[str, Any]]:
    """Select activities that fit within the available time"""
    selected = []
    remaining_time = available_time
    
    for activity in activities:
        activity_duration = activity.get("duration_hours", 0)
        
        # Add buffer time between activities (15 minutes)
        buffer_time = 0.25 if selected else 0
        
        if activity_duration + buffer_time <= remaining_time:
            selected.append(activity)
            remaining_time -= (activity_duration + buffer_time)
        else:
            # If this activity doesn't fit, try to find a shorter alternative
            continue
    
    print(f"[Itinerary] Selected {len(selected)} activities for {available_time}h")
    return selected

def _order_activities_logically(activities: List[Dict[str, Any]], start_time: str = None) -> List[Dict[str, Any]]:
    """Order activities in a logical sequence"""
    if len(activities) <= 1:
        return activities
    
    # Start with the highest confidence activity
    ordered = [activities[0]]
    remaining = activities[1:]
    
    # Add activities considering:
    # 1. Energy level progression (start low, build up, end low)
    # 2. Activity type variety
    # 3. Location proximity (simplified)
    
    while remaining:
        best_next = _find_best_next_activity(ordered, remaining)
        if best_next:
            ordered.append(best_next)
            remaining.remove(best_next)
        else:
            # If no good next activity found, add the highest confidence remaining
            ordered.append(remaining[0])
            remaining.pop(0)
    
    # Assign start times if provided
    if start_time:
        _assign_start_times(ordered, start_time)
    
    return ordered

def _find_best_next_activity(current_sequence: List[Dict[str, Any]], remaining: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the best next activity based on logical progression"""
    if not remaining:
        return None
    
    current_energy = current_sequence[-1].get("energy_level", 5)
    current_type = current_sequence[-1].get("activity_type", "general")
    
    # Score remaining activities
    scored_activities = []
    for activity in remaining:
        score = 0
        activity_energy = activity.get("energy_level", 5)
        activity_type = activity.get("activity_type", "general")
        
        # Prefer energy level progression (slight increase or decrease)
        energy_diff = abs(activity_energy - current_energy)
        if energy_diff <= 2:
            score += 0.3
        elif energy_diff <= 3:
            score += 0.1
        
        # Prefer different activity types for variety
        if activity_type != current_type:
            score += 0.2
        
        # Prefer higher confidence activities
        score += activity.get("confidence", 0) * 0.5
        
        scored_activities.append((score, activity))
    
    # Return the highest scoring activity
    scored_activities.sort(key=lambda x: x[0], reverse=True)
    return scored_activities[0][1] if scored_activities else None

def _assign_start_times(activities: List[Dict[str, Any]], start_time: str):
    """Assign start times to activities"""
    try:
        # Parse start time
        start_hour, start_minute = map(int, start_time.split(":"))
        current_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        for activity in activities:
            activity["start_time"] = current_time.strftime("%H:%M")
            
            # Add duration to get next start time
            duration_hours = activity.get("duration_hours", 1)
            duration_minutes = int(duration_hours * 60)
            current_time += timedelta(minutes=duration_minutes + 15)  # 15 min buffer
            
    except Exception as e:
        print(f"[Itinerary] Error assigning start times: {e}")

def _generate_itinerary_summary(activities: List[Dict[str, Any]], total_duration: float, total_cost: float) -> str:
    """Generate a human-readable summary of the itinerary"""
    if not activities:
        return "No activities planned."
    
    activity_types = {}
    indoor_outdoor_counts = {"indoor": 0, "outdoor": 0}
    
    for activity in activities:
        activity_type = activity.get("activity_type", "general")
        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        indoor_outdoor = activity.get("indoor_outdoor", "indoor")
        indoor_outdoor_counts[indoor_outdoor] += 1
    
    # Create summary text
    summary_parts = []
    
    # Duration and cost
    summary_parts.append(f"Your {total_duration:.1f}-hour itinerary costs approximately ${total_cost:.0f}")
    
    # Activity types
    if activity_types:
        type_descriptions = []
        for activity_type, count in activity_types.items():
            if count == 1:
                type_descriptions.append(f"a {activity_type} activity")
            else:
                type_descriptions.append(f"{count} {activity_type} activities")
        
        summary_parts.append(f"Featuring {', '.join(type_descriptions)}")
    
    # Indoor/outdoor balance
    if indoor_outdoor_counts["indoor"] > 0 and indoor_outdoor_counts["outdoor"] > 0:
        summary_parts.append("with a mix of indoor and outdoor experiences")
    elif indoor_outdoor_counts["outdoor"] > 0:
        summary_parts.append("focusing on outdoor activities")
    elif indoor_outdoor_counts["indoor"] > 0:
        summary_parts.append("focusing on indoor activities")
    
    return ". ".join(summary_parts) + "."
