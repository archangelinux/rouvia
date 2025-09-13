'use client';

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';


// const MAPBOX_TOKEN = process.env['NEXT_PUBLIC_MAPBOX_TOKEN'];
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN //'pk.eyJ1IjoiY2xhaXJlbGV1IiwiYSI6ImNtZmhyZHRpeTBlbTcybHB0Z2h0MWViaWwifQ.3WtsGrkviDv9WhvPkFGeKw';

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
      pitch: 45, // 3D perspective
      bearing: 0,
      antialias: true
    });

    console.log("created new map");

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    // Add some sample markers (based on the image)
    const markers = [
      { name: 'Kik', coordinates: [11.5761, 48.1374], type: 'clothing' },
      { name: 'Norma', coordinates: [11.5771, 48.1384], type: 'store' },
      { name: 'zplatz', coordinates: [11.5751, 48.1364], type: 'location' }
    ];

    markers.forEach(marker => {
      const el = document.createElement('div');
      el.className = 'marker';
      el.style.cssText = `
        background-color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 2px solid ${marker.type === 'location' ? '#10b981' : '#3b82f6'};
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      `;

      // Add appropriate icon
      const iconMap = {
        clothing: '👕',
        store: '🛒', 
        location: '📍'
      };
      el.textContent = iconMap[marker.type as keyof typeof iconMap];

      new mapboxgl.Marker(el)
        .setLngLat(marker.coordinates as [number, number])
        .addTo(map.current!);
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
