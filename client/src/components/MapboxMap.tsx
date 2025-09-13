"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import type { LineString } from "geojson";
import "mapbox-gl/dist/mapbox-gl.css";

const MAPBOX_TOKEN =
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "YOUR_MAPBOX_TOKEN_HERE";

function buildDirectionsUrl(
  profile: "driving" | "walking" | "cycling",
  coords: [number, number][]
): string {
  const path = coords.map(([lon, lat]) => `${lon},${lat}`).join(";");
  const params = new URLSearchParams({
    geometries: "geojson",
    steps: "true",
    overview: "full",
    access_token: MAPBOX_TOKEN!,
  });
  return `https://api.mapbox.com/directions/v5/mapbox/${profile}/${path}?${params.toString()}`;
}

declare global {
  interface Window {
    __routeMarkers?: mapboxgl.Marker[];
  }
}

export default function MapboxMap() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;
    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === "YOUR_MAPBOX_TOKEN_HERE") {
      console.warn("Missing Mapbox token. Set NEXT_PUBLIC_MAPBOX_TOKEN.");
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: [11.5761, 48.1374],
      zoom: 13,
      antialias: true,
    });
    mapRef.current = map;

    map.addControl(new mapboxgl.NavigationControl(), "bottom-right");

    const waypoints: [number, number][] = [
      [11.5761, 48.1374], // Start: Marienplatz
      [11.5785, 48.1379], // East of start
      [11.5792, 48.1395], // North-east
      [11.5778, 48.1405], // Towards Hofgarten
      [11.5753, 48.1401], // West side
      [11.574, 48.1386], // Back down
      [11.5771, 48.1384], // End: near your original endpoint
    ];
    const directionsUrl = buildDirectionsUrl("walking", waypoints);

    map.on("load", () => {
      (async () => {
        try {
          const res = await fetch(directionsUrl);
          const data = await res.json();

          const geometry = data?.routes?.[0]?.geometry as
            | LineString
            | undefined;
          if (!geometry) {
            console.error("No route returned:", data);
            return;
          }

          const routeSourceId = "route";
          const routeLayerId = "route-line";

          if (map.getSource(routeSourceId)) {
            (map.getSource(routeSourceId) as mapboxgl.GeoJSONSource).setData({
              type: "Feature",
              properties: {},
              geometry,
            });
          } else {
            map.addSource(routeSourceId, {
              type: "geojson",
              data: {
                type: "Feature",
                properties: {},
                geometry,
              },
            });

            map.addLayer({
              id: routeLayerId,
              type: "line",
              source: routeSourceId,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: {
                "line-width": 5,
                "line-color": "#3b82f6",
              },
            });
          }

          // Clear old markers (HMR-safe)
          if (window.__routeMarkers) {
            window.__routeMarkers.forEach((m) => m.remove());
          }
          const newMarkers: mapboxgl.Marker[] = [];

          if (waypoints.length > 0) {
            newMarkers.push(
              new mapboxgl.Marker({ color: "green" })
                .setLngLat(waypoints[0])
                .addTo(map)
            );
          }
          if (waypoints.length > 1) {
            newMarkers.push(
              new mapboxgl.Marker({ color: "red" })
                .setLngLat(waypoints[waypoints.length - 1])
                .addTo(map)
            );
          }
          window.__routeMarkers = newMarkers;

          const coords = geometry.coordinates as [number, number][];
          const bounds = coords.reduce(
            (b, c) => b.extend(c),
            new mapboxgl.LngLatBounds(coords[0], coords[0])
          );
          map.fitBounds(bounds, { padding: 50, duration: 800 });
        } catch (e) {
          console.error("Failed to load route:", e);
        }
      })();
    });

    return () => {
      if (window.__routeMarkers) {
        window.__routeMarkers.forEach((m) => m.remove());
        window.__routeMarkers = undefined;
      }
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);
  console.log("Mapbox token in client:", process.env.NEXT_PUBLIC_MAPBOX_TOKEN);
  return (
    <div
      ref={mapContainer}
      className="absolute inset-0 w-full h-full"
      aria-label="Mapbox map container"
    />
  );
}
