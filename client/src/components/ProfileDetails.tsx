'use client';

import React, { useState, useEffect } from "react";
import { logout } from '@/lib/auth0';
import { X, Plus, Edit, Trash2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

interface Location {
  id?: string;
  name: string;
  address: string;
  lat?: number;
  lng?: number;
  place_id?: string;
  added_at?: string;
}

interface UserProfile {
  auth0_user_id: string;
  email: string;
  name?: string;
  keywords: Record<string, Location>;
  visited_places: any[];
  preferences: any;
  created_at: string;
  last_login?: string;
  last_updated: string;
}

interface ProfileDetailsProps {
  onClose: () => void;
  user?: {
    name?: string | null;
    email?: string | null;
  };
}

interface LocationSearchModalProps {
  location: Location;
  keyword: string;
  onSave: (keyword: string, location: Location) => void;
  onClose: () => void;
}

interface AddLocationModalProps {
  onSave: (keyword: string, location: Location) => void;
  onClose: () => void;
}

// LocationSearchModal Component
function LocationSearchModal({ location, keyword, onSave, onClose }: LocationSearchModalProps) {
  const [query, setQuery] = useState(location.address);
  const [results, setResults] = useState<Array<{place_name: string, center: [number, number], place_id?: string}>>([]);
  const [locationName, setLocationName] = useState(location.name);
  const [selectedLocation, setSelectedLocation] = useState<{place_name: string, center: [number, number], place_id?: string} | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const fetchLocations = async () => {
      // Try Google Maps API first if available, fallback to Mapbox
      if (GOOGLE_MAPS_API_KEY) {
        try {
          const response = await fetch(
            `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(
              query
            )}&key=${GOOGLE_MAPS_API_KEY}&types=establishment|geocode`
          );
          
          if (!response.ok) {
            throw new Error(`Google Places API error: ${response.status}`);
          }
          
          const data = await response.json();
          
          if (data.predictions && Array.isArray(data.predictions)) {
            // For Google Places, we need to get place details to get coordinates
            const placesWithCoords = await Promise.all(
              data.predictions.slice(0, 4).map(async (prediction: any) => {
                try {
                  const detailsResponse = await fetch(
                    `https://maps.googleapis.com/maps/api/place/details/json?place_id=${prediction.place_id}&fields=name,formatted_address,geometry&key=${GOOGLE_MAPS_API_KEY}`
                  );
                  const detailsData = await detailsResponse.json();
                  
                  if (detailsData.result) {
                    return {
                      place_name: detailsData.result.formatted_address,
                      center: [detailsData.result.geometry.location.lng, detailsData.result.geometry.location.lat],
                      place_id: prediction.place_id
                    };
                  }
                  return null;
                } catch (err) {
                  console.error("Error fetching place details:", err);
                  return null;
                }
              })
            );
            
            setResults(placesWithCoords.filter(Boolean));
        return;
          }
        } catch (err) {
          console.error("Error with Google Places API:", err);
        }
      }

      // Fallback to Mapbox
      if (MAPBOX_TOKEN) {
      try {
        const response = await fetch(
          `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
            query
          )}.json?access_token=${MAPBOX_TOKEN}&autocomplete=true&limit=4`
        );
        
        if (!response.ok) {
          throw new Error(`Mapbox API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.features && Array.isArray(data.features)) {
            const places = data.features.map((f: any) => ({
              place_name: f.place_name,
              center: f.center,
              place_id: f.id
            }));
          setResults(places);
          }
        } catch (err) {
          console.error("Error fetching locations:", err);
          setResults([]);
        }
      } else {
        console.warn("No mapping API token configured. Location search disabled.");
        setResults([]);
      }
    };

    fetchLocations();
  }, [query]);

  const handleSave = () => {
    const locationData = selectedLocation || {
      place_name: query,
      center: [location.lng || 0, location.lat || 0],
      place_id: location.place_id
    };
    
    onSave(keyword, {
      ...location,
      name: locationName,
      address: locationData.place_name,
      lat: locationData.center[1],
      lng: locationData.center[0],
      place_id: locationData.place_id
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
              placeholder={MAPBOX_TOKEN ? "Search for a location" : "Enter location manually (search disabled)"}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />

            {!MAPBOX_TOKEN && (
              <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Location search is disabled. Please enter addresses manually.
                </p>
              </div>
            )}
            
            {results.length > 0 && !selectedLocation && (
              <div className="mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                {results.map((place, index) => (
                  <div
                    key={index}
                    className={`p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0 ${
                      selectedLocation?.place_name === place.place_name ? 'bg-blue-50 border-blue-200' : ''
                    }`}
                    onClick={() => {
                      setQuery(place.place_name);
                      setSelectedLocation(place);
                    }}
                  >
                    <div className="font-medium">{place.place_name}</div>
                    <div className="text-sm text-gray-500">
                      Lat: {place.center[1].toFixed(4)}, Lng: {place.center[0].toFixed(4)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedLocation && (
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-800">Selected Location:</p>
                    <p className="text-sm text-green-700">{selectedLocation.place_name}</p>
                    <p className="text-xs text-green-600">
                      Lat: {selectedLocation.center[1].toFixed(4)}, Lng: {selectedLocation.center[0].toFixed(4)}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedLocation(null)}
                    className="text-green-600 hover:text-green-800 text-sm"
                  >
                    Change
                  </button>
                </div>
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

// AddLocationModal Component
function AddLocationModal({ onSave, onClose }: AddLocationModalProps) {
  const [keyword, setKeyword] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Array<{place_name: string, center: [number, number], place_id?: string}>>([]);
  const [selectedLocation, setSelectedLocation] = useState<{place_name: string, center: [number, number], place_id?: string} | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const fetchLocations = async () => {
      // Try Google Maps API first if available, fallback to Mapbox
      if (GOOGLE_MAPS_API_KEY) {
        try {
          const response = await fetch(
            `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(
              query
            )}&key=${GOOGLE_MAPS_API_KEY}&types=establishment|geocode`
          );
          
          if (!response.ok) {
            throw new Error(`Google Places API error: ${response.status}`);
          }
          
          const data = await response.json();
          
          if (data.predictions && Array.isArray(data.predictions)) {
            // For Google Places, we need to get place details to get coordinates
            const placesWithCoords = await Promise.all(
              data.predictions.slice(0, 4).map(async (prediction: any) => {
                try {
                  const detailsResponse = await fetch(
                    `https://maps.googleapis.com/maps/api/place/details/json?place_id=${prediction.place_id}&fields=name,formatted_address,geometry&key=${GOOGLE_MAPS_API_KEY}`
                  );
                  const detailsData = await detailsResponse.json();
                  
                  if (detailsData.result) {
                    return {
                      place_name: detailsData.result.formatted_address,
                      center: [detailsData.result.geometry.location.lng, detailsData.result.geometry.location.lat],
                      place_id: prediction.place_id
                    };
                  }
                  return null;
                } catch (err) {
                  console.error("Error fetching place details:", err);
                  return null;
                }
              })
            );
            
            setResults(placesWithCoords.filter(Boolean));
            return;
          }
        } catch (err) {
          console.error("Error with Google Places API:", err);
        }
      }

      // Fallback to Mapbox
      if (MAPBOX_TOKEN) {
        try {
          const response = await fetch(
            `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(
              query
            )}.json?access_token=${MAPBOX_TOKEN}&autocomplete=true&limit=4`
          );
          
          if (!response.ok) {
            throw new Error(`Mapbox API error: ${response.status} ${response.statusText}`);
          }
          
          const data = await response.json();
          
          if (data.features && Array.isArray(data.features)) {
            const places = data.features.map((f: any) => ({
              place_name: f.place_name,
              center: f.center,
              place_id: f.id
            }));
            setResults(places);
          }
        } catch (err) {
          console.error("Error fetching locations:", err);
          setResults([]);
        }
      } else {
        console.warn("No mapping API token configured. Location search disabled.");
        setResults([]);
      }
    };

    fetchLocations();
  }, [query]);

  const handleSave = () => {
    if (!keyword.trim() || !selectedLocation) {
      alert('Please enter a keyword and select a location');
      return;
    }

    onSave(keyword.trim(), {
      name: keyword.trim(),
      address: selectedLocation.place_name,
      lat: selectedLocation.center[1],
      lng: selectedLocation.center[0],
      place_id: selectedLocation.place_id
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Add New Location</h3>
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
              Keyword (e.g., Home, Work, School)
            </label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Enter a keyword for this location"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Address
            </label>
            <input
              type="text"
              placeholder={(GOOGLE_MAPS_API_KEY || MAPBOX_TOKEN) ? "Search for a location" : "Enter location manually (search disabled)"}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />

            {!GOOGLE_MAPS_API_KEY && !MAPBOX_TOKEN && (
              <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Location search is disabled. Please enter addresses manually.
                </p>
              </div>
            )}
            
            {results.length > 0 && !selectedLocation && (
              <div className="mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                {results.map((place, index) => (
                  <div
                    key={index}
                    className={`p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0 ${
                      selectedLocation?.place_name === place.place_name ? 'bg-blue-50 border-blue-200' : ''
                    }`}
                    onClick={() => {
                      setQuery(place.place_name);
                      setSelectedLocation(place);
                    }}
                  >
                    <div className="font-medium">{place.place_name}</div>
                    <div className="text-sm text-gray-500">
                      Lat: {place.center[1].toFixed(4)}, Lng: {place.center[0].toFixed(4)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedLocation && (
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-800">Selected Location:</p>
                    <p className="text-sm text-green-700">{selectedLocation.place_name}</p>
                    <p className="text-xs text-green-600">
                      Lat: {selectedLocation.center[1].toFixed(4)}, Lng: {selectedLocation.center[0].toFixed(4)}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedLocation(null)}
                    className="text-green-600 hover:text-green-800 text-sm"
                  >
                    Change
                  </button>
                </div>
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

export default function ProfileDetails({ onClose, user }: ProfileDetailsProps) {
  const { user: auth0User, logout } = useAuth();
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingLocation, setEditingLocation] = useState<{keyword: string, location: Location} | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load user profile from MongoDB
  useEffect(() => {
    const loadUserProfile = async () => {
      if (!auth0User?.sub) {
        setError('Please log in to view your profile');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/user-profile/${auth0User.sub}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            setError('Profile not found. Please try logging in again.');
            return;
          }
          throw new Error('Failed to load profile');
        }
        
        const data = await response.json();
        setUserProfile(data.profile);
      } catch (err) {
        console.error('Error loading user profile:', err);
        setError('Failed to load profile. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadUserProfile();
  }, [auth0User?.sub]);

  const handleEditLocation = (keyword: string, location: Location) => {
    setEditingLocation({ keyword, location });
  };

  const handleSaveLocation = async (keyword: string, updatedLocation: Location) => {
    if (!auth0User?.sub) {
      alert('Please log in to save locations');
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/user-profile/${auth0User.sub}/keywords`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keyword,
          location: updatedLocation
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save location');
      }

      // Update local state
      setUserProfile(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          keywords: {
            ...prev.keywords,
            [keyword]: updatedLocation
          }
        };
      });

      setEditingLocation(null);
    } catch (err) {
      console.error('Error saving location:', err);
      alert('Failed to save location. Please try again.');
    }
  };

  const handleAddNewLocation = (keyword: string, location: Location) => {
    handleSaveLocation(keyword, location);
    setShowAddModal(false);
  };

  const handleDeleteLocation = async (keyword: string) => {
    if (!auth0User?.sub) {
      alert('Please log in to delete locations');
      return;
    }

    if (!confirm(`Are you sure you want to delete the "${keyword}" location?`)) {
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/user-profile/${auth0User.sub}/keywords/${encodeURIComponent(keyword)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete location');
      }

      // Update local state
      setUserProfile(prev => {
        if (!prev) return prev;
        const newKeywords = { ...prev.keywords };
        delete newKeywords[keyword];
        return {
          ...prev,
          keywords: newKeywords
        };
      });
    } catch (err) {
      console.error('Error deleting location:', err);
      alert('Failed to delete location. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-white z-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-white z-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️</div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={onClose}
            className="bg-gray-800 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const keywords = userProfile?.keywords || {};

  return (
    <div className="fixed inset-0 bg-white z-50 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div>
          <h1 className="text-3xl font-bold text-black">
            {user?.name || 'User'}
          </h1>
          <p className="text-lg text-gray-600 mt-1">
            {user?.email || 'user@example.com'}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={async () => {
              try {
                console.log('Signing out...');
                await logout();
              } catch (error) {
                console.error('Sign out error:', error);
                // Fallback: clear storage and redirect
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = '/landing';
              }
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
        {/* Section Header */}
        <h2 className="text-xl font-semibold text-gray-800 mb-6">My locations</h2>
        
        {/* Locations List */}
        <div className="space-y-0">
          {Object.keys(keywords).length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">📍</div>
              <h3 className="text-lg font-medium text-gray-600 mb-2">No locations added yet</h3>
              <p className="text-gray-500 mb-6">Add your first location to get started</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2 mx-auto"
              >
                <Plus size={20} />
                <span>Add Location</span>
              </button>
            </div>
          ) : (
            Object.entries(keywords).map(([keyword, location], index) => (
              <div key={keyword}>
              {/* Separator line above each location */}
              {index > 0 && (
                <div className="border-t border-gray-200 my-4"></div>
              )}
              
              {/* Location Row */}
              <div className="flex items-start justify-between py-6">
                <div className="flex-1 space-y-2">
                  <div className="bg-gray-50 rounded-lg px-4 py-3">
                      <h3 className="text-lg font-bold text-black">{keyword}</h3>
                  </div>
                  <div className="bg-blue-50 rounded-lg px-4 py-3">
                    <p className="text-base text-gray-700">{location.address}</p>
                      {location.lat && location.lng && (
                        <p className="text-sm text-gray-500 mt-1">
                          📍 {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="ml-4 flex space-x-2">
                  <button
                      onClick={() => handleEditLocation(keyword, location)}
                    className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors flex items-center space-x-2"
                  >
                    <Edit size={16} />
                    <span>Edit</span>
                  </button>
                    <button
                      onClick={() => handleDeleteLocation(keyword)}
                      className="bg-red-100 text-red-700 px-4 py-2 rounded-lg hover:bg-red-200 transition-colors flex items-center space-x-2"
                    >
                      <Trash2 size={16} />
                      <span>Delete</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Add New Location Button */}
        {Object.keys(keywords).length > 0 && (
        <div className="flex justify-center mt-8">
          <button
              onClick={() => setShowAddModal(true)}
            className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
          >
            <Plus size={20} />
              <span>Add Location</span>
          </button>
        </div>
        )}
      </div>

      {/* Location Search Modal */}
      {editingLocation && (
        <LocationSearchModal
          location={editingLocation.location}
          keyword={editingLocation.keyword}
          onSave={handleSaveLocation}
          onClose={() => setEditingLocation(null)}
        />
      )}

      {/* Add Location Modal */}
      {showAddModal && (
        <AddLocationModal
          onSave={handleAddNewLocation}
          onClose={() => setShowAddModal(false)}
        />
      )}
    </div>
  );
}