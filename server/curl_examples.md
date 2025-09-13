# Sidequest API Test Examples

## Quick Test Commands

### 1. Basic Multi-Interest Sidequest
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 5.0,
    "start_time": "10:00",
    "end_time": "16:00",
    "budget": 100,
    "interests": ["entertainment", "meals", "shopping"],
    "energy": 6,
    "indoor_outdoor": "mixed",
    "user_id": "test_user_1"
  }'
```

### 2. Short Time Priority Test (2 hours)
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 3.0,
    "start_time": "14:00",
    "end_time": "16:00",
    "budget": 50,
    "interests": ["meals", "bites", "entertainment"],
    "energy": 4,
    "indoor_outdoor": "indoor",
    "user_id": "test_user_1"
  }'
```

### 3. Full Day Meal Limit Test (8 hours)
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 10.0,
    "start_time": "09:00",
    "end_time": "17:00",
    "budget": 200,
    "interests": ["meals", "entertainment", "scenery", "shopping"],
    "energy": 7,
    "indoor_outdoor": "mixed",
    "user_id": "test_user_1"
  }'
```

### 4. Physical Activity Focus
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 8.0,
    "start_time": "08:00",
    "end_time": "14:00",
    "budget": 75,
    "interests": ["physical_activity", "scenery", "bites"],
    "energy": 9,
    "indoor_outdoor": "outdoor",
    "user_id": "test_user_1"
  }'
```

### 5. Budget Constrained
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 5.0,
    "start_time": "11:00",
    "end_time": "15:00",
    "budget": 25,
    "interests": ["scenery", "entertainment"],
    "energy": 5,
    "indoor_outdoor": "mixed",
    "user_id": "test_user_1"
  }'
```

### 6. New User Test
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 5.0,
    "start_time": "12:00",
    "end_time": "18:00",
    "budget": 80,
    "interests": ["entertainment", "meals"],
    "energy": 6,
    "indoor_outdoor": "mixed",
    "user_id": "new_user_123"
  }'
```

### 7. Invalid Interests Fallback
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 5.0,
    "start_time": "13:00",
    "end_time": "17:00",
    "budget": 60,
    "interests": ["invalid_interest", "another_invalid"],
    "energy": 5,
    "indoor_outdoor": "mixed",
    "user_id": "test_user_1"
  }'
```

### 8. No Interests Default
```bash
curl -X POST http://localhost:8000/sidequest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 43.4643,
    "lon": -80.5204,
    "travel_distance": 5.0,
    "start_time": "10:00",
    "end_time": "14:00",
    "budget": 40,
    "energy": 5,
    "indoor_outdoor": "mixed",
    "user_id": "test_user_1"
  }'
```

## Expected Results

### Validation Rules
- ✅ **One per interest**: Each interest category gets exactly one activity
- ✅ **Meal limits**: Max 3 meals/day, 2 meals/half day
- ✅ **Unvisited places**: At least one activity must be new
- ✅ **Time priority**: Short time prioritizes meals + entertainment over bites
- ✅ **Food spreading**: Meals spread throughout the day
- ✅ **Fallback**: Invalid interests fallback to entertainment

### Interest Categories
- `shopping` - Shopping centers, markets, stores
- `meals` - Full meals, restaurants
- `bites` - Snacks, cafes, quick bites
- `entertainment` - Events, shows, entertainment venues
- `physical_activity` - Sports, hiking, active pursuits
- `scenery` - Parks, viewpoints, scenic locations

### Response Format
```json
{
  "itinerary": [
    {
      "title": "Activity Name",
      "location": "Address",
      "start_time": "10:00",
      "duration_hours": 1.5,
      "cost": 25,
      "activity_type": "entertainment",
      "indoor_outdoor": "indoor",
      "energy_level": 5,
      "confidence": 0.8,
      "description": "Brief description",
      "highlights": "Key features"
    }
  ],
  "total_duration": 6.0,
  "total_cost": 75,
  "summary": "Your 6-hour sidequest includes...",
  "metadata": {
    "activities_considered": 50,
    "activities_selected": 3,
    "activities_in_itinerary": 3,
    "interests_covered": ["entertainment", "meals", "shopping"],
    "unvisited_places": 2
  }
}
```

## Running Tests

### Using the Shell Script
```bash
./test_sidequest_api.sh
```

### Using Python Script
```bash
python test_sidequest.py
```

### Using Individual Curl Commands
Copy and paste any of the curl commands above into your terminal.
