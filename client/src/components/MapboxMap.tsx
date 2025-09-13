'use client';

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';


// const MAPBOX_TOKEN = process.env['NEXT_PUBLIC_MAPBOX_TOKEN'];
const MAPBOX_TOKEN = process.env['NEXT_PUBLIC_MAPBOX_TOKEN'];

export default function MapboxMap() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    //if (map.current) return; // Initialize map only once
    if (!mapContainer.current) return; // checks the div is rendered

    // Check if we have a valid Mapbox token
    if (!MAPBOX_TOKEN) {
      console.warn('Mapbox token is null');
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [11.5761, 48.1374], // Munich coordinates (based on the image)
      zoom: 15,
      pitch: 60, // More dramatic 3D perspective
      bearing: 0,
      antialias: true
    });

    console.log("created new map");

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    // Add some sample markers (based on the image)
    const markers = [
      { name: 'Kik', coordinates: [11.5761, 48.1374], type: 'clothing', icon: '👕' },
      { name: 'Norma', coordinates: [11.5771, 48.1384], type: 'store', icon: '🛒' },
      { name: 'Litzplatz', coordinates: [11.5751, 48.1364], type: 'park', icon: '🌳' },
      { name: 'BMW Forschung und Technik GmbH', coordinates: [11.5781, 48.1394], type: 'building', icon: '🏢' },
      { name: 'Georg-Brauchle-Ring', coordinates: [11.5741, 48.1354], type: 'landmark', icon: '🏛️' }
    ];

    markers.forEach(marker => {
      const el = document.createElement('div');
      el.className = 'marker';
      el.style.cssText = `
        background-color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid ${marker.type === 'park' ? '#10b981' : '#3b82f6'};
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        font-size: 16px;
        cursor: pointer;
        transition: transform 0.2s ease;
      `;

      el.textContent = marker.icon;

      // Add hover effect
      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.1)';
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
      });

      const markerInstance = new mapboxgl.Marker(el)
        .setLngLat(marker.coordinates as [number, number])
        .addTo(map.current!);

      // Add popup with marker name
      const popup = new mapboxgl.Popup({ offset: 25 })
        .setHTML(`<div class="text-sm font-medium">${marker.name}</div>`);
      
      markerInstance.setPopup(popup);
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  return <div ref={mapContainer} className="absolute inset-0 w-full h-full" />;

  // If no valid Mapbox token, show placeholder
  if (!MAPBOX_TOKEN) {
    return (
      <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
        {/* Placeholder map background with city-like pattern */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-20 left-20 w-32 h-32 bg-gray-400 rounded-lg transform rotate-12"></div>
          <div className="absolute top-40 left-60 w-24 h-24 bg-gray-500 rounded-lg transform -rotate-12"></div>
          <div className="absolute top-60 left-40 w-28 h-28 bg-gray-400 rounded-lg transform rotate-6"></div>
          <div className="absolute top-80 left-80 w-20 h-20 bg-gray-500 rounded-lg transform -rotate-6"></div>
          <div className="absolute top-32 left-120 w-36 h-36 bg-gray-400 rounded-lg transform rotate-12"></div>
        </div>
        
        {/* Sample markers with proper styling */}
        <div className="absolute top-20 left-20 w-8 h-8 bg-white rounded-full border-2 border-blue-500 flex items-center justify-center text-sm shadow-lg">
          👕
        </div>
        <div className="absolute top-40 left-60 w-8 h-8 bg-white rounded-full border-2 border-blue-500 flex items-center justify-center text-sm shadow-lg">
          🛒
        </div>
        <div className="absolute top-60 left-40 w-8 h-8 bg-white rounded-full border-2 border-green-500 flex items-center justify-center text-sm shadow-lg">
          📍
        </div>
        
        {/* Map controls */}
        <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
          <button className="w-10 h-10 bg-white rounded shadow-lg flex items-center justify-center text-gray-600 hover:bg-gray-50">
            +
          </button>
          <button className="w-10 h-10 bg-white rounded shadow-lg flex items-center justify-center text-gray-600 hover:bg-gray-50">
            −
          </button>
        </div>
      </div>
    );
  }
}
