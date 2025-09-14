"use client";

import { createContext, useContext, useMemo, useState, ReactNode } from "react";

export type PlaceStop = {
  place_id: string;
  name: string;
  address: string;
  lat: number;
  lng: number;
  rating?: number;
  user_ratings_total?: number;
  types?: string[];
  google_maps_uri?: string;
  website_uri?: string | null;
  business_status?: string;
  // Sidequest-specific fields
  start_time?: string;
  duration_hours?: number;
  cost?: number;
  activity_type?: string;
  indoor_outdoor?: string;
  energy_level?: number;
  confidence?: number;
};

type Waypoint = [number, number]; // [lng, lat] for Mapbox

type RouteContextValue = {
  userLocation: { latitude: number; longitude: number } | null;
  setUserLocation: (
    loc: { latitude: number; longitude: number } | null
  ) => void;

  stops: PlaceStop[];
  setStops: (s: PlaceStop[]) => void;

  waypoints: Waypoint[]; // derived or explicitly set
  setWaypoints: (w: Waypoint[]) => void;
};

const RouteContext = createContext<RouteContextValue | null>(null);

export function RouteProvider({ children }: { children: ReactNode }) {
  const [userLocation, setUserLocation] =
    useState<RouteContextValue["userLocation"]>(null);
  const [stops, setStops] = useState<PlaceStop[]>([]);
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);

  const value = useMemo<RouteContextValue>(
    () => ({
      userLocation,
      setUserLocation,
      stops,
      setStops,
      waypoints,
      setWaypoints,
    }),
    [userLocation, stops, waypoints]
  );

  return (
    <RouteContext.Provider value={value}>{children}</RouteContext.Provider>
  );
}

export function useRoute() {
  const ctx = useContext(RouteContext);
  if (!ctx) throw new Error("useRoute must be used inside <RouteProvider>");
  return ctx;
}
