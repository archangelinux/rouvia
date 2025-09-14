'use client';

import { useState } from 'react';
import { Wand2, Sparkles } from 'lucide-react';
import { useRoute, type PlaceStop } from "@/components/context/route-context";

interface FilterState {
  energy: number;
  interests: {
    shopping: boolean;
    food: boolean;
    entertainment: boolean;
    scenery: boolean;
  };
  budget: number;
  time: {
    start: string;
    end: string;
  };
  indoorOutdoor: {
    indoor: boolean;
    outdoor: boolean;
  };
  distance: string;
}

async function getUserLocation(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        resolve({ latitude, longitude });
      },
      (error) => {
        reject(error);
      },
      { enableHighAccuracy: true }
    );
  });
}

// Type for the API response based on the schema
type SidequestActivity = {
  title: string;
  lat: number;
  lon: number;
  start_time?: string;
  duration_hours: number;
  cost?: number;
  activity_type: string;
  indoor_outdoor: string;
  energy_level: number;
  confidence: number;
};

type SidequestResponse = {
  itinerary: SidequestActivity[];
  total_duration: number;
  total_cost: number;
  summary: string;
  metadata: {
    activities_considered: number;
    activities_selected: number;
    activities_in_itinerary: number;
    generation_time?: string;
  };
};

// Helper function to map SidequestActivity to PlaceStop
function mapActivityToPlaceStop(activity: SidequestActivity, index: number): PlaceStop {
  return {
    place_id: `sidequest-${index}-${activity.title}-${activity.lat},${activity.lon}`,
    name: activity.title,
    address: "", // API doesn't provide address
    lat: activity.lat,
    lng: activity.lon,
    // Optional fields could be added here if needed
    types: [activity.activity_type],
  };
}

export default function FilterPanel() {
  const { setUserLocation, setStops, setWaypoints } = useRoute();
  
  const [filters, setFilters] = useState<FilterState>({
    energy: 5,
    interests: {
      shopping: false,
      food: false,
      entertainment: false,
      scenery: false,
    },
    budget: 0,
    time: {
      start: '09:00',
      end: '17:00',
    },
    indoorOutdoor: {
      indoor: false,
      outdoor: false,
    },
    distance: '5',
  });

  const handleEnergyChange = (value: number) => {
    setFilters(prev => ({ ...prev, energy: value }));
  };

  const handleBudgetChange = (value: number) => {
    setFilters(prev => ({ ...prev, budget: value }));
  };

  const handleInterestChange = (interest: keyof FilterState['interests']) => {
    setFilters(prev => ({
      ...prev,
      interests: {
        ...prev.interests,
        [interest]: !prev.interests[interest],
      },
    }));
  };

  const handleTimeChange = (field: 'start' | 'end', value: string) => {
    setFilters(prev => ({
      ...prev,
      time: {
        ...prev.time,
        [field]: value,
      },
    }));
  };

  const handleIndoorOutdoorChange = (type: keyof FilterState['indoorOutdoor']) => {
    setFilters(prev => ({
      ...prev,
      indoorOutdoor: {
        ...prev.indoorOutdoor,
        [type]: !prev.indoorOutdoor[type],
      },
    }));
  };

  const handleDistanceChange = (value: string) => {
    setFilters(prev => ({ ...prev, distance: value }));
  };

  const handleGenerateSidequest = async () => {
    // Validate distance field
    if (filters.distance.trim() === '') {
      alert('Please enter a distance value');
      return;
    }

    const distanceNumber = parseFloat(filters.distance);
    if (isNaN(distanceNumber) || distanceNumber < 0) {
      alert('Distance must be a valid positive number');
      return;
    }

    // Get user location
    let location;
    try {
      location = await getUserLocation();
      console.log("User location:", location.latitude, location.longitude);
      setUserLocation(location); // Update route context
    } catch (err) {
      console.error("Failed to get location:", err);
      alert("Please enable location access and try again.");
      return;
    }

    // Get selected interests as array of strings
    const selectedInterests = Object.keys(filters.interests)
      .filter(key => filters.interests[key as keyof typeof filters.interests]);

    // Get selected indoor/outdoor preference as string or null
    const selectedIndoorOutdoor = 
      filters.indoorOutdoor.indoor && filters.indoorOutdoor.outdoor ? null :
      filters.indoorOutdoor.indoor ? "indoor" :
      filters.indoorOutdoor.outdoor ? "outdoor" : null;

    const sidequestData = {
      "lat": location.latitude,
      "lon": location.longitude,
      "travel_distance": distanceNumber,
      "start_time": filters.time.start,
      "end_time": filters.time.end,
      "budget": filters.budget > 0 ? filters.budget : null,
      "interests": selectedInterests,
      "energy": filters.energy,
      "indoor_outdoor": selectedIndoorOutdoor,
      "user_id": "test_user",
    };

    console.log('Sending sidequest data:', sidequestData);

    try {
      const response = await fetch('http://localhost:8000/sidequest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sidequestData),
      });

      if (response.ok) {
        const result: SidequestResponse = await response.json();
        console.log('Raw sidequest response:', result);

        // Map activities to PlaceStop objects
        const placeStops: PlaceStop[] = result.itinerary.map(mapActivityToPlaceStop);
        console.log('Mapped place stops:', placeStops);

        // Update route context
        setStops(placeStops);

        // Create waypoints: user location + all activity locations
        const waypoints: [number, number][] = [
          [location.longitude, location.latitude], // User location first
          ...placeStops.map(stop => [stop.lng, stop.lat])
        ];
        setWaypoints(waypoints);

        console.log('Route context updated:', {
          userLocation: location,
          stops: placeStops,
          waypoints: waypoints,
        });

        alert(`Sidequest generated! ${result.itinerary.length} activities planned. Total duration: ${result.total_duration.toFixed(1)} hours.`);
      } else {
        const errorText = await response.text();
        console.error('Failed to generate sidequest:', response.status, errorText);
        alert('Failed to generate sidequest. Please try again.');
      }
    } catch (error) {
      console.error('Error generating sidequest:', error);
      alert('Unexpected error while generating sidequest.');
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
      <div className="space-y-6">
        {/* Energy Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Energy (0-10)</label>
          <div className="relative">
            <input
              type="range"
              min="0"
              max="10"
              value={filters.energy}
              onChange={(e) => handleEnergyChange(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #10b981 0%, #10b981 ${((filters.energy) / 10) * 100}%, #e5e7eb ${((filters.energy) / 10) * 100}%, #e5e7eb 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>0</span>
              <span className="text-green-600 font-medium">{filters.energy}</span>
              <span>10</span>
            </div>
          </div>
        </div>

        {/* Interests Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Interests</label>
          <div className="grid grid-cols-2 gap-2">
            {(['shopping', 'food', 'entertainment', 'scenery'] as const).map((interest) => (
              <label key={interest} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.interests[interest]}
                  onChange={() => handleInterestChange(interest)}
                  className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                />
                <span className="text-sm text-gray-700 capitalize">{interest}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Budget Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Budget</label>
          <div className="relative">
            <input
              type="range"
              min="0"
              max="400"
              value={filters.budget}
              onChange={(e) => handleBudgetChange(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #10b981 0%, #10b981 ${(filters.budget / 400) * 100}%, #e5e7eb ${(filters.budget / 400) * 100}%, #e5e7eb 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>$0</span>
              <span className="text-green-600 font-medium">${filters.budget}</span>
              <span>$400</span>
            </div>
          </div>
        </div>

        {/* Time Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Time (24hr)</label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Start</label>
              <input
                type="time"
                value={filters.time.start}
                onChange={(e) => handleTimeChange('start', e.target.value)}
                className="w-full px-3 py-2 border-0 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-green-50 text-green-700"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">End</label>
              <input
                type="time"
                value={filters.time.end}
                onChange={(e) => handleTimeChange('end', e.target.value)}
                className="w-full px-3 py-2 border-0 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-green-50 text-green-700"
              />
            </div>
          </div>
        </div>

        {/* Indoor/Outdoor Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-5">Indoor/Outdoor</label>
          <div className="flex gap-3">
            {(['indoor', 'outdoor'] as const).map((type) => (
              <label key={type} className="flex items-center space-x-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.indoorOutdoor[type]}
                  onChange={() => handleIndoorOutdoorChange(type)}
                  className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                />
                <span className="text-sm text-gray-700 capitalize">{type}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Sidequest Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Max Distance (km)</label>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={filters.distance}
              onChange={(e) => handleDistanceChange(e.target.value)}
              placeholder="(km)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-green-500"
            />
          </div>
        </div>

        {/* Generate Sidequest Button */}
        <div className="pt-4">
          <button
            onClick={handleGenerateSidequest}
            className="w-full bg-green-500 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-600 transition-colors flex items-center justify-center space-x-2"
          >
            <Wand2 size={18} />
            <span>Generate Sidequest</span>
          </button>
        </div>
      </div>
    </div>
  );
}