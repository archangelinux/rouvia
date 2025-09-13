"""
Fast weighted scoring system for activity selection
"""
import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ScoringWeights:
    """User-customizable scoring weights"""
    cost_weight: float = 0.3      # How much cost matters (0-1)
    distance_weight: float = 0.3  # How much distance matters (0-1) 
    rating_weight: float = 0.2    # How much rating matters (0-1)
    trendiness_weight: float = 0.2 # Fixed weight for trendiness boost

class ActivityScorer:
    def __init__(self, user_weights: Optional[ScoringWeights] = None):
        self.weights = user_weights or ScoringWeights()
    
    def calculate_base_scores(self, activities: List[Dict[str, Any]], 
                            user_lat: float, user_lon: float, 
                            budget: float) -> List[Dict[str, Any]]:
        """
        Calculate base scores for all activities using only Google Places data.
        Fast - no API calls to Cohere.
        """
        scored_activities = []
        
        for activity in activities:
            # Extract data from structured field
            structured = activity.get("structured", {})
            lat = structured.get("lat", 0)
            lon = structured.get("lon", 0)
            rating = structured.get("rating", 0)
            cost = structured.get("cost", 0)
            
            # Calculate individual scores (0-1 scale)
            cost_score = self._calculate_cost_score(cost, budget)
            distance_score = self._calculate_distance_score(lat, lon, user_lat, user_lon)
            rating_score = self._calculate_rating_score(rating)
            
            # Calculate weighted base score
            base_score = (
                cost_score * self.weights.cost_weight +
                distance_score * self.weights.distance_weight +
                rating_score * self.weights.rating_weight
            )
            
            # Add scores to activity
            activity_with_scores = activity.copy()
            activity_with_scores.update({
                "cost_score": cost_score,
                "distance_score": distance_score, 
                "rating_score": rating_score,
                "base_score": base_score,
                "trendiness_score": 0.5,  # Default neutral
                "final_score": base_score  # Will be updated with trendiness
            })
            
            scored_activities.append(activity_with_scores)
        
        return scored_activities
    
    def apply_trendiness_boost(self, activities: List[Dict[str, Any]], 
                             trendiness_data: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Apply trendiness boost to activities based on Cohere analysis.
        Only called for top candidates to keep it fast.
        """
        for activity in activities:
            structured = activity.get("structured", {})
            place_name = structured.get("name", "")
            trendiness = trendiness_data.get(place_name.lower(), 0.5)  # Default neutral
            
            activity["trendiness_score"] = trendiness
            
            # Recalculate final score with trendiness
            activity["final_score"] = (
                activity["base_score"] + 
                trendiness * self.weights.trendiness_weight
            )
        
        return activities
    
    def _calculate_cost_score(self, cost: float, budget: float) -> float:
        """Calculate cost score (0-1, higher is better)"""
        if budget <= 0:
            return 0.5  # Neutral if no budget constraint
        
        if cost <= 0:
            return 1.0  # Free is always good
        
        # Score decreases as cost approaches budget
        ratio = cost / budget
        if ratio >= 1.0:
            return 0.0  # Over budget
        elif ratio >= 0.8:
            return 0.2  # Close to budget limit
        elif ratio >= 0.5:
            return 0.6  # Moderate cost
        else:
            return 1.0  # Well under budget
    
    def _calculate_distance_score(self, lat: float, lon: float, 
                                user_lat: float, user_lon: float) -> float:
        """Calculate distance score (0-1, higher is closer)"""
        if lat == 0 or lon == 0:
            return 0.5  # Unknown location
        
        # Simple distance calculation (not precise but fast)
        distance = math.sqrt((lat - user_lat)**2 + (lon - user_lon)**2)
        
        # Convert to score (closer = higher score)
        if distance <= 0.01:  # Very close (~1km)
            return 1.0
        elif distance <= 0.05:  # Close (~5km)
            return 0.8
        elif distance <= 0.1:   # Moderate (~10km)
            return 0.6
        elif distance <= 0.2:   # Far (~20km)
            return 0.4
        else:
            return 0.2  # Very far
    
    def _calculate_rating_score(self, rating: float) -> float:
        """Calculate rating score (0-1, higher is better)"""
        if rating <= 0:
            return 0.5  # Unknown rating
        
        # Normalize 1-5 scale to 0-1
        return (rating - 1) / 4
    
    def select_top_candidates(self, activities: List[Dict[str, Any]], 
                            per_category: int = 5) -> List[Dict[str, Any]]:
        """
        Select top candidates per interest category for trendiness analysis.
        This keeps Cohere calls minimal.
        """
        # Group by activity type
        by_category = {}
        for activity in activities:
            activity_type = activity.get("activity_type", "general")
            if activity_type not in by_category:
                by_category[activity_type] = []
            by_category[activity_type].append(activity)
        
        # Select top N per category
        top_candidates = []
        for category, category_activities in by_category.items():
            # Sort by base score and take top N
            sorted_activities = sorted(category_activities, 
                                     key=lambda x: x["base_score"], 
                                     reverse=True)
            top_candidates.extend(sorted_activities[:per_category])
        
        return top_candidates

# Global instance
activity_scorer = ActivityScorer()
