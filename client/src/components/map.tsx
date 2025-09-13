"use client";

import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';

import 'mapbox-gl/dist/mapbox-gl.css';

const MapboxExample = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;
    console.log("Mapbox token:", process.env.NEXT_PUBLIC_MAPBOX_TOKEN);
    mapboxgl.accessToken = 'pk.eyJ1IjoiY2xhaXJlbGV1IiwiYSI6ImNtZmhyZHRpeTBlbTcybHB0Z2h0MWViaWwifQ.3WtsGrkviDv9WhvPkFGeKw'
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [-74.5, 40], // starting position [lng, lat]
      zoom: 9 // starting zoom
    });
  });

  return (
    <div
      style={{ height: '100%' }}
      ref={mapContainerRef}
      className="map-container"
    />
  );
};

export default MapboxExample;
