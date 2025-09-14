'use client';

import React, { useState, useEffect } from "react";
import { X, Plus, Edit } from 'lucide-react';

const MAPBOX_TOKEN =process.env['NEXT_PUBLIC_MAPBOX_TOKEN']

interface Location {
  id: string;
  name: string;
  address: string;
}

interface ProfileDetailsProps {
  onClose: () => void;
}

interface LocationSearchModalProps {
  location: Location;
  onSave: (location: Location) => void;
  onClose: () => void;
}

// LocationSearchModal Component
function LocationSearchModal({ location, onSave, onClose }: LocationSearchModalProps) {
  const [query, setQuery] = useState(location.address);
  const [results, setResults] = useState<string[]>([]);
  const [locationName, setLocationName] = useState(location.name);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }

    const fetchLocations = async () => {
      try {
        const response = await fetch(
          `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
            query
          )}.json?access_token=${MAPBOX_TOKEN}&autocomplete=true&limit=4`
        );
        const data = await response.json();
        const places = data.features.map((f: any) => f.place_name);
        setResults(places);
        setShowResults(true);
      } catch (err) {
        console.error("Error fetching locations:", err);
      }
    };

    fetchLocations();
  }, [query]);

  const handleSave = () => {
    onSave({
      ...location,
      name: locationName,
      address: query
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Edit Location</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location Name
            </label>
            <input
              type="text"
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="e.g., Home, Work, School"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Address
            </label>
            <input
              type="text"
              placeholder="Search for a location"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setShowResults(false);
                }
              }}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />

            {showResults && results.length > 0 && (
              <div className="mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                {results.map((place, index) => (
                  <div
                    key={index}
                    className="p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                    onClick={() => {
                      setQuery(place);
                      setShowResults(false);
                    }}
                  >
                    {place}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleSave}
              className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors"
            >
              Save
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProfileDetails({ onClose }: ProfileDetailsProps) {
  const [locations, setLocations] = useState<Location[]>([
    {
      id: '1',
      name: 'Home',
      address: '423 Mayorview Dr, Burlington, ON L4E 9W2'
    },
    {
      id: '2',
      name: 'Work',
      address: '1003 Bloor St, Toronto, ON N2J 2J9'
    },
    {
      id: '3',
      name: 'School',
      address: '81 Wellington St N, Kitchener, ON N2H 5K2'
    },
    {
      id: '4',
      name: 'Daycare',
      address: '200 Columbia St W, Waterloo, ON N2L 3L3'
    }
  ]);
  const [editingLocation, setEditingLocation] = useState<Location | null>(null);

  const handleEditLocation = (id: string) => {
    const location = locations.find(loc => loc.id === id);
    if (location) {
      setEditingLocation(location);
    }
  };

  const handleSaveLocation = (updatedLocation: Location) => {
    setLocations(prev => 
      prev.map(loc => 
        loc.id === updatedLocation.id ? updatedLocation : loc
      )
    );
    setEditingLocation(null);
  };

  const handleAddNewLocation = () => {
    // TODO: Implement add new location functionality
    console.log('Add new location');
  };

  return (
    <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div>
          <h1 className="text-3xl font-bold text-black">Jack Russell</h1>
          <p className="text-lg text-gray-600 mt-1">My locations</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              // TODO: Implement logout functionality
              console.log('Logout clicked');
            }}
            className="bg-gray-800 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Logout
          </button>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X size={24} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto p-6">
        {/* Locations List */}
        <div className="space-y-0">
          {locations.map((location, index) => (
            <div key={location.id}>
              {/* Separator line above each location */}
              {index > 0 && (
                <div className="border-t border-gray-200 my-4"></div>
              )}
              
              {/* Location Row */}
              <div className="flex items-center justify-between py-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <h3 className="text-lg font-bold text-black">{location.name}</h3>
                    <p className="text-base text-gray-700">{location.address}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleEditLocation(location.id)}
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors flex items-center space-x-2"
                >
                  <Edit size={16} />
                  <span>Edit</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add New Location Button */}
        <div className="flex justify-center mt-8">
          <button
            onClick={handleAddNewLocation}
            className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
          >
            <Plus size={20} />
            <span>New Item</span>
          </button>
        </div>
      </div>

      {/* Location Search Modal */}
      {editingLocation && (
        <LocationSearchModal
          location={editingLocation}
          onSave={handleSaveLocation}
          onClose={() => setEditingLocation(null)}
        />
      )}
    </div>
  );
}
