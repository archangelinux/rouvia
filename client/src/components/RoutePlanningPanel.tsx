'use client';

import { useState } from 'react';
import { Play, Plus, MapPin } from 'lucide-react';

interface RouteStop {
  id: string;
  name: string;
  address?: string;
  isActive?: boolean;
}

interface RouteSegment {
  id: string;
  instruction: string;
  duration: string;
  distance: string;
}

export default function RoutePlanningPanel() {
  const [stops, setStops] = useState<RouteStop[]>([
    { id: '1', name: 'Your location', isActive: false },
    { id: '2', name: 'University of Waterloo Stat', isActive: true },
    { id: '3', name: 'Waterloo Park', isActive: false },
    { id: '4', name: "Vincenzo's", isActive: false },
  ]);

  const [segments] = useState<RouteSegment[]>([
    { id: '1', instruction: 'Via Columbia Way', duration: '1 min', distance: '190 m' },
    { id: '2', instruction: 'Continue to Erb St. West', duration: '5 min', distance: '1.2 km' },
  ]);

  const totalDuration = '1hr 12 min';

  const addStop = () => {
    const newStop: RouteStop = {
      id: Date.now().toString(),
      name: 'New stop',
      isActive: false,
    };
    setStops(prev => [...prev, newStop]);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 max-h-[60vh] overflow-y-auto">
      {/* Route Line with Stops */}
      <div className="relative mb-6">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-green-500"></div>
        
        {stops.map((stop, index) => (
          <div key={stop.id} className="relative flex items-center mb-4">
            <div className={`w-3 h-3 rounded-full border-2 z-10 ${
              stop.isActive 
                ? 'bg-green-500 border-green-500' 
                : 'bg-white border-gray-300'
            }`}></div>
            
            <div className="ml-4 flex-1">
              <input
                type="text"
                value={stop.name}
                onChange={(e) => {
                  setStops(prev => prev.map(s => 
                    s.id === stop.id ? { ...s, name: e.target.value } : s
                  ));
                }}
                className={`w-full px-3 py-2 rounded-lg border text-sm ${
                  stop.name === 'Your location' 
                    ? 'bg-gray-100 text-gray-500 border-gray-200' 
                    : 'bg-white border-gray-300 focus:border-green-500 focus:outline-none'
                }`}
                placeholder={stop.name === 'Your location' ? 'Your location' : 'Enter destination'}
                disabled={stop.name === 'Your location'}
              />
            </div>
          </div>
        ))}
        
        {/* Add Stop Button */}
        <div className="relative flex items-center">
          <div className="w-3 h-3 rounded-full border-2 border-dashed border-gray-300"></div>
          <button
            onClick={addStop}
            className="ml-4 flex items-center text-sm text-gray-500 hover:text-green-600 transition-colors"
          >
            <Plus size={16} className="mr-1" />
            Add stop
          </button>
        </div>
      </div>

      {/* Route Details */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm font-medium text-gray-700">
          <span>Total time</span>
          <span className="text-green-600">{totalDuration}</span>
        </div>
        
        {segments.map((segment, index) => (
          <div key={segment.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <MapPin size={14} className="text-gray-400 mr-2" />
              <span className="text-sm text-gray-700">{segment.instruction}</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-xs text-gray-500">{segment.duration} ({segment.distance})</span>
              {index === 1 && (
                <button className="bg-green-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-green-600 transition-colors flex items-center">
                  <Play size={14} className="mr-1" />
                  Start
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
