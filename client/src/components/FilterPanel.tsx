'use client';

import { useState } from 'react';
import { MessageCircle, Sparkles, Wand2 } from 'lucide-react';

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

export default function FilterPanel() {
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
    distance: '',
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
    } catch (err) {
      console.error("Failed to get location:", err);
      location = null;
    }

    if(!location) {
      console.log("Location not found, line 157 FilterPanel.tsx")
      return (
        <div>
          <p>Please enable location access and try again.</p>
        </div>
      )
    }

    const sidequestData = {
      "lat": location.latitude,
      "lon": location.longitude,
      "travel_distance": distanceNumber,
      "start_time": filters.time.start,
      "end_time": filters.time.end,
      "budget": filters.budget,
      "interests": Object.keys(filters.interests)
      .filter(key => String(filters.interests[key as keyof typeof filters.interests])[0]) || "",
      "energy": filters.energy,
      "indoor_outdoor": filters.indoorOutdoor.indoor ? "indoor" : "outdoor",
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
        const result = await response.json();
        console.log('Sidequest generated:', result);
        
        // Return well-structured JSON object with all input parameters
        const structuredResponse = {
          inputParameters: {
            lat: location.latitude,
            lon: location.longitude,
            energy: filters.energy,
            interests: Object.keys(filters.interests).filter(key => filters.interests[key as keyof typeof filters.interests]),
            budget: filters.budget,
            time: {
              start: filters.time.start,
              end: filters.time.end,
            },
            indoorOutdoor: Object.keys(filters.indoorOutdoor).filter(key => filters.indoorOutdoor[key as keyof typeof filters.indoorOutdoor]),
            distance: distanceNumber,
          },
          generatedSidequest: result,
          timestamp: new Date().toISOString(),
          status: 'success'
        };
        
        console.log('Structured response:', structuredResponse);
        return structuredResponse;
      } else {
        console.error('Failed to generate sidequest');
        const errorResponse = {
          inputParameters: {
            latitude: location.latitude,
            longitude: location.longitude,
            energy: filters.energy,
            interests: Object.keys(filters.interests).filter(key => filters.interests[key as keyof typeof filters.interests]),
            budget: filters.budget,
            time: {
              start: filters.time.start,
              end: filters.time.end,
            },
            indoorOutdoor: Object.keys(filters.indoorOutdoor).filter(key => filters.indoorOutdoor[key as keyof typeof filters.indoorOutdoor]),
            distance: distanceNumber,
          },
          error: 'Failed to generate sidequest',
          timestamp: new Date().toISOString(),
          status: 'error'
        };
        console.log('Error response:', errorResponse);
        return errorResponse;
      }
    } catch (error) {
      console.error('Error generating sidequest:', error);
      const errorResponse = {
        inputParameters: {
          location: {
            latitude: location.latitude,
            longitude: location.longitude,
          },
          energy: filters.energy,
          interests: Object.keys(filters.interests).filter(key => filters.interests[key as keyof typeof filters.interests]),
          budget: filters.budget,
          time: {
            start: filters.time.start,
            end: filters.time.end,
          },
          indoorOutdoor: Object.keys(filters.indoorOutdoor).filter(key => filters.indoorOutdoor[key as keyof typeof filters.indoorOutdoor]),
          distance: distanceNumber,
        },
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        timestamp: new Date().toISOString(),
        status: 'error'
      };
      console.log('Error response:', errorResponse);
      return errorResponse;
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

        {/* Distance Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Distance</label>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={filters.distance}
              onChange={(e) => handleDistanceChange(e.target.value)}
              placeholder="(km)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-green-500"
            />
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <MessageCircle size={16} />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <Sparkles size={16} />
            </button>
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
