'use client';

import { useState } from 'react';
import { MessageCircle, Sparkles } from 'lucide-react';

interface FilterState {
  distance: string;
  price: number;
  activityLevel: {
    high: boolean;
    medium: boolean;
    low: boolean;
  };
  activityType: {
    food: boolean;
    shopping: boolean;
    social: boolean;
  };
}

export default function FilterPanel() {
  const [filters, setFilters] = useState<FilterState>({
    distance: '',
    price: 0,
    activityLevel: {
      high: false,
      medium: false,
      low: false,
    },
    activityType: {
      food: false,
      shopping: false,
      social: false,
    },
  });

  const handleDistanceChange = (value: string) => {
    setFilters(prev => ({ ...prev, distance: value }));
  };

  const handlePriceChange = (value: number) => {
    setFilters(prev => ({ ...prev, price: value }));
  };

  const handleActivityLevelChange = (level: keyof FilterState['activityLevel']) => {
    setFilters(prev => ({
      ...prev,
      activityLevel: {
        ...prev.activityLevel,
        [level]: !prev.activityLevel[level],
      },
    }));
  };

  const handleActivityTypeChange = (type: keyof FilterState['activityType']) => {
    setFilters(prev => ({
      ...prev,
      activityType: {
        ...prev.activityType,
        [type]: !prev.activityType[type],
      },
    }));
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
      <div className="space-y-6">
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

        {/* Price Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Price</label>
          <div className="relative">
            <input
              type="range"
              min="0"
              max="400"
              value={filters.price}
              onChange={(e) => handlePriceChange(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>$0</span>
              <span className="text-green-600 font-medium">${filters.price}</span>
              <span>$400</span>
            </div>
          </div>
        </div>

        {/* Activity Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Activity</label>
          <div className="grid grid-cols-2 gap-4">
            {/* Activity Level */}
            <div className="space-y-2">
              <div className="text-xs text-gray-500 mb-2">Level</div>
              {(['high', 'medium', 'low'] as const).map((level) => (
                <label key={level} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.activityLevel[level]}
                    onChange={() => handleActivityLevelChange(level)}
                    className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{level}</span>
                </label>
              ))}
            </div>

            {/* Activity Type */}
            <div className="space-y-2">
              <div className="text-xs text-gray-500 mb-2">Type</div>
              {(['food', 'shopping', 'social'] as const).map((type) => (
                <label key={type} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.activityType[type]}
                    onChange={() => handleActivityTypeChange(type)}
                    className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
