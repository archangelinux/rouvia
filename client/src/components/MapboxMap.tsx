// MapboxMap.tsx
"use client";

import { useEffect, useMemo, useRef } from "react";
import mapboxgl from "mapbox-gl";
import type { LineString } from "geojson";
import "mapbox-gl/dist/mapbox-gl.css";
import { useRoute } from "@/components/context/route-context";

const MAPBOX_TOKEN =
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "YOUR_MAPBOX_TOKEN_HERE";

type LngLat = [number, number];

function buildDirectionsUrl(
  profile: "driving" | "walking" | "cycling",
  coords: LngLat[]
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

// Consider two points the same if within ~0.5m (1e-5 deg ~ 1.1m at equator)
function nearlySame([aLng, aLat]: LngLat, [bLng, bLat]: LngLat) {
  return Math.abs(aLng - bLng) < 1e-5 && Math.abs(aLat - bLat) < 1e-5;
}

declare global {
  interface Window {
    __routeMarkers?: mapboxgl.Marker[];
  }
}

export default function MapboxMap() {
  const { waypoints, stops, userLocation } = useRoute();
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  // Build the effective list of points to render:
  // If we have userLocation, prepend it unless it's basically the same as the first waypoint.
  const points: LngLat[] = useMemo(() => {
    const raw = Array.isArray(waypoints) ? waypoints.slice() : [];
    if (userLocation) {
      const userPt: LngLat = [userLocation.longitude, userLocation.latitude];
      if (!raw[0] || !nearlySame(raw[0], userPt)) return [userPt, ...raw];
    }
    return raw;
  }, [waypoints, userLocation]);

  // Initialize the map once
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
      center: [-80.524, 43.464], // Waterloo-ish default
      zoom: 12,
      antialias: true,
    });
    map.addControl(new mapboxgl.NavigationControl(), "bottom-right");
    mapRef.current = map;

    return () => {
      if (window.__routeMarkers) {
        window.__routeMarkers.forEach((m) => m.remove());
        window.__routeMarkers = undefined;
      }
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Render/update route + markers whenever points/stops change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const ROUTE_SOURCE_ID = "route";
    const ROUTE_LAYER_ID = "route-line";

    // Helper: clear route layer/source
    const clearRoute = () => {
      if (map.getLayer(ROUTE_LAYER_ID)) map.removeLayer(ROUTE_LAYER_ID);
      if (map.getSource(ROUTE_SOURCE_ID)) map.removeSource(ROUTE_SOURCE_ID);
    };

    // Helper: clear markers
    const clearMarkers = () => {
      if (window.__routeMarkers) {
        window.__routeMarkers.forEach((m) => m.remove());
        window.__routeMarkers = undefined;
      }
    };

    // Start with a clean slate each update
    clearMarkers();

    // If no points, nothing to render
    if (!Array.isArray(points) || points.length === 0) {
      clearRoute();
      return;
    }

    // If only one point, drop a single marker and center
    if (points.length === 1) {
      clearRoute();
      const only = points[0];
      const marker = createMarkerForIndex(0, only, stops).addTo(map);
      window.__routeMarkers = [marker];
      map.flyTo({ center: only, zoom: 14 });
      return;
    }

    // With 2+ points: fetch directions and draw route
    const url = buildDirectionsUrl("walking", points);
    const controller = new AbortController();

    const render = async () => {
      try {
        const res = await fetch(url, { signal: controller.signal });
        const data = await res.json();

        const geometry = data?.routes?.[0]?.geometry as LineString | undefined;
        if (!geometry) {
          console.error("No route returned:", data);
          // Still show markers even if route failed
          const markers = points.map((p, i) =>
            createMarkerForIndex(i, p, stops).addTo(map)
          );
          window.__routeMarkers = markers;
          fitToMarkers(map, points);
          return;
        }

        const addOrUpdate = () => {
          if (map.getSource(ROUTE_SOURCE_ID)) {
            (map.getSource(ROUTE_SOURCE_ID) as mapboxgl.GeoJSONSource).setData({
              type: "Feature",
              properties: {},
              geometry,
            });
          } else {
            map.addSource(ROUTE_SOURCE_ID, {
              type: "geojson",
              data: { type: "Feature", properties: {}, geometry },
            });
            map.addLayer({
              id: ROUTE_LAYER_ID,
              type: "line",
              source: ROUTE_SOURCE_ID,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: { "line-width": 5, "line-color": "#3b82f6" },
            });
          }
        };

        if (!map.isStyleLoaded()) map.once("load", addOrUpdate);
        else addOrUpdate();

        // Add markers for every point (0 = You)
        const markers = points.map((p, i) =>
          createMarkerForIndex(i, p, stops).addTo(map)
        );
        window.__routeMarkers = markers;

        // Fit to the route geometry
        const coords = geometry.coordinates as LngLat[];
        fitToBounds(map, coords);
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error("Failed to load route:", err);
        // Fall back to markers only
        clearRoute();
        const markers = points.map((p, i) =>
          createMarkerForIndex(i, p, stops).addTo(map)
        );
        window.__routeMarkers = markers;
        fitToMarkers(map, points);
      }
    };

    render();

    return () => {
      controller.abort();
    };
  }, [points, stops]);

  return (
    <div
      ref={mapContainer}
      className="absolute inset-0 w-full h-full"
      aria-label="Mapbox map container"
    />
  );
}

/** Create a styled marker + popup for index i (0 = user). */
function createMarkerForIndex(
  i: number,
  lngLat: [number, number],
  stops: ReturnType<typeof useRoute>["stops"]
) {
  const el = document.createElement("div");
  el.style.width = "26px";
  el.style.height = "26px";
  el.style.borderRadius = "9999px";
  el.style.display = "flex";
  el.style.alignItems = "center";
  el.style.justifyContent = "center";
  el.style.fontSize = "12px";
  el.style.fontWeight = "700";
  el.style.boxShadow = "0 2px 8px rgba(0,0,0,0.25)";

  let popupHtml: string;

  if (i === 0) {
    // User location pin
    el.style.background = "#2563eb"; // blue
    el.style.color = "white";
    el.textContent = "You";
    popupHtml = `<strong>You</strong><div style="opacity:.8">Current location</div>`;
  } else {
    // Stop pins start at 1 and map to stops[i-1]
    el.style.background = "#111827"; // near-black
    el.style.color = "white";
    el.textContent = String(i);

    const s = stops?.[i - 1];
    if (!s) {
      popupHtml = `<strong>Stop ${i}</strong>`;
    } else {
      const name = s.name ?? `Stop ${i}`;
      const addr = s.address
        ? `<div style="opacity:.8">${s.address}</div>`
        : "";
      const rating =
        s.rating != null
          ? `<div style="margin-top:4px;font-size:12px;opacity:.8">Rating: ${
              s.rating
            } (${s.user_ratings_total ?? 0})</div>`
          : "";
      const link = s.google_maps_uri
        ? `<div style="margin-top:6px"><a href="${s.google_maps_uri}" target="_blank" rel="noopener noreferrer">Open in Google Maps</a></div>`
        : "";
      popupHtml = `<strong>${name}</strong>${addr}${rating}${link}`;
    }
  }

  return new mapboxgl.Marker({ element: el })
    .setLngLat(lngLat)
    .setPopup(new mapboxgl.Popup({ offset: 12 }).setHTML(popupHtml));
}

/** Fit to a set of coordinates (route geometry). */
function fitToBounds(map: mapboxgl.Map, coords: [number, number][]) {
  if (!coords?.length) return;
  const bounds = coords.reduce(
    (b, c) => b.extend(c),
    new mapboxgl.LngLatBounds(coords[0], coords[0])
  );
  map.fitBounds(bounds, { padding: 50, duration: 800 });
}

/** Fit to marker positions when no route is available. */
function fitToMarkers(map: mapboxgl.Map, pts: [number, number][]) {
  if (!pts?.length) return;
  if (pts.length === 1) {
    map.flyTo({ center: pts[0], zoom: 14 });
    return;
  }
  fitToBounds(map, pts);
}
