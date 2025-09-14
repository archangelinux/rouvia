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

// -----------------------------
// Helpers
// -----------------------------
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

// ~0.5 m threshold (1e-5° ~1.1 m at equator)
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

  // Compute points to render (prepend user location if present & not duplicate)
  const points: LngLat[] = useMemo(() => {
    const raw = Array.isArray(waypoints) ? waypoints.slice() : [];
    if (userLocation) {
      const userPt: LngLat = [userLocation.longitude, userLocation.latitude];
      if (!raw[0] || !nearlySame(raw[0], userPt)) return [userPt, ...raw];
    }
    return raw;
  }, [waypoints, userLocation]);

  // -----------------------------
  // Map init (3D setup)
  // -----------------------------
  useEffect(() => {
    if (!mapContainer.current) return;
    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === "YOUR_MAPBOX_TOKEN_HERE") {
      console.warn("Missing Mapbox token. Set NEXT_PUBLIC_MAPBOX_TOKEN.");
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v12", // has composite source for buildings
      center: userLocation
        ? [userLocation.longitude, userLocation.latitude] // 👈 use user location
        : [-80.524, 43.464],
      zoom: 12,
      pitch: 0, // 👈 tilt for 3D
      bearing: 0, // 👈 rotate for depth
      antialias: true, // smoother edges for 3D layers
    });

    // Better 3D gesture controls
    map.dragRotate.enable();
    map.touchZoomRotate.enableRotation();
    map.addControl(new mapboxgl.NavigationControl(), "bottom-right");

    // When style is ready, add terrain, sky, fog, and 3D buildings
    const onLoad = () => {
      // DEM terrain source
      if (!map.getSource("mapbox-dem")) {
        map.addSource("mapbox-dem", {
          type: "raster-dem",
          url: "mapbox://mapbox.mapbox-terrain-dem-v1",
          tileSize: 512,
          maxzoom: 14,
        });
      }
      map.setTerrain({ source: "mapbox-dem", exaggeration: 1.3 });

      // Atmospheric sky
      if (!map.getLayer("sky")) {
        map.addLayer({
          id: "sky",
          type: "sky",
          paint: {
            "sky-type": "atmosphere",
            "sky-atmosphere-sun": [0.0, 0.0],
            "sky-atmosphere-sun-intensity": 12,
          },
        });
      }

      // Optional fog for distance depth
      map.setFog({
        range: [0.5, 10],
        "horizon-blend": 0.1,
        color: "white",
        "high-color": "#add8e6",
        "space-color": "#000000",
      } as mapboxgl.Fog);

      // Insert 3D buildings below label layers so labels stay readable
      const layers = map.getStyle().layers ?? [];
      const labelLayerId = layers.find(
        (l: any) => l.type === "symbol" && l.layout && l.layout["text-field"]
      )?.id;

      if (!map.getLayer("3d-buildings")) {
        map.addLayer(
          {
            id: "3d-buildings",
            source: "composite",
            "source-layer": "building",
            filter: ["==", "extrude", "true"],
            type: "fill-extrusion",
            minzoom: 12,
            paint: {
              "fill-extrusion-color": "#aaa",
              "fill-extrusion-height": ["get", "height"],
              "fill-extrusion-base": ["get", "min_height"],
              "fill-extrusion-opacity": 0.6,
            },
          },
          labelLayerId
        );
      }
    };

    if (map.isStyleLoaded()) onLoad();
    else map.once("load", onLoad);

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

  // -----------------------------
  // Route + markers rendering
  // -----------------------------
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const ROUTE_SOURCE_ID = "route";
    const ROUTE_LAYER_ID = "route-line";

    const clearRoute = () => {
      if (map.getLayer(ROUTE_LAYER_ID)) map.removeLayer(ROUTE_LAYER_ID);
      if (map.getSource(ROUTE_SOURCE_ID)) map.removeSource(ROUTE_SOURCE_ID);
    };

    const clearMarkers = () => {
      if (window.__routeMarkers) {
        window.__routeMarkers.forEach((m) => m.remove());
        window.__routeMarkers = undefined;
      }
    };

    clearMarkers();

    if (!Array.isArray(points) || points.length === 0) {
      clearRoute();
      return;
    }

    // Single point: show a marker and center
    if (points.length === 1) {
      clearRoute();
      const only = points[0];
      const marker = createMarkerForIndex(0, only, stops).addTo(map);
      window.__routeMarkers = [marker];

      // Keep the 3D angle when flying
      map.easeTo({
        center: only,
        zoom: 14,
        pitch: map.getPitch(),
        bearing: map.getBearing(),
        duration: 600,
      });
      return;
    }

    // 2+ points: fetch directions and draw route
    const url = buildDirectionsUrl("walking", points);
    const controller = new AbortController();

    const render = async () => {
      try {
        const res = await fetch(url, { signal: controller.signal });
        const data = await res.json();
        const geometry = data?.routes?.[0]?.geometry as LineString | undefined;

        if (!geometry) {
          console.error("No route returned:", data);
          const markers = points.map((p, i) =>
            createMarkerForIndex(i, p, stops).addTo(map)
          );
          window.__routeMarkers = markers;
          map.easeTo({ pitch: 60, bearing: -17.6, duration: 600 });
          fitToMarkers(map, points);
          return;
        }

        const addOrUpdate = () => {
          const feature = { type: "Feature", properties: {}, geometry };
          if (map.getSource(ROUTE_SOURCE_ID)) {
            (map.getSource(ROUTE_SOURCE_ID) as mapboxgl.GeoJSONSource).setData(
              feature as any
            );
          } else {
            map.addSource(ROUTE_SOURCE_ID, { type: "geojson", data: feature });
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

        // Markers
        const markers = points.map((p, i) =>
          createMarkerForIndex(i, p, stops).addTo(map)
        );
        window.__routeMarkers = markers;

        // Animate into a nice 3D camera, then fit to route
        map.easeTo({ pitch: 60, bearing: -17.6, duration: 600 });
        const coords = geometry.coordinates as LngLat[];
        fitToBounds(map, coords);
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error("Failed to load route:", err);
        clearRoute();
        const markers = points.map((p, i) =>
          createMarkerForIndex(i, p, stops).addTo(map)
        );
        window.__routeMarkers = markers;
        map.easeTo({ pitch: 60, bearing: -17.6, duration: 600 });
        fitToMarkers(map, points);
      }
    };

    render();
    return () => controller.abort();
  }, [points, stops]);

  return (
    <div
      ref={mapContainer}
      className="absolute inset-0 w-full h-full"
      aria-label="Mapbox map container (3D)"
    />
  );
}

// -----------------------------
// Marker / Camera utilities
// -----------------------------

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
    el.style.background = "#2563eb"; // blue
    el.style.color = "white";
    el.textContent = "You";
    popupHtml = `<strong>You</strong><div style="opacity:.8">Current location</div>`;
  } else {
    el.style.background = "#111827"; // near-black
    el.style.color = "white";
    el.textContent = String(i);

    const s = stops?.[i - 1] as any;
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

/** Fit to a set of coordinates (route geometry) without resetting 3D angle. */
function fitToBounds(map: mapboxgl.Map, coords: [number, number][]) {
  if (!coords?.length) return;
  const bounds = coords.reduce(
    (b, c) => b.extend(c),
    new mapboxgl.LngLatBounds(coords[0], coords[0])
  );
  map.fitBounds(bounds, {
    padding: 50,
    duration: 800,
    pitch: map.getPitch(),
    bearing: map.getBearing(),
  });
}

/** Fit to marker positions when no route is available. */
function fitToMarkers(map: mapboxgl.Map, pts: [number, number][]) {
  if (!pts?.length) return;
  if (pts.length === 1) {
    map.easeTo({
      center: pts[0],
      zoom: 14,
      duration: 600,
      pitch: map.getPitch(),
      bearing: map.getBearing(),
    });
    return;
  }
  fitToBounds(map, pts);
}
