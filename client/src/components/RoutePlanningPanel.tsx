// RoutePlanningPanel.tsx
"use client";

import { useMemo, useState } from "react";
import { Loader2, Play, Plus } from "lucide-react";
import { useRoute, type PlaceStop } from "@/components/context/route-context";

type UiStop =
  | { kind: "origin"; id: "origin"; name: "Your location"; disabled: true }
  | {
      kind: "place";
      id: string;
      name: string;
      disabled?: false;
      place: PlaceStop;
    };

type LngLat = [number, number];

type StepItem = {
  text: string;
  distance: number; // meters
  mainInstruction: string;
  subInstruction: string;
};

const MAPBOX_TOKEN =
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "YOUR_MAPBOX_TOKEN_HERE";

/** Directions URL builder */
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

/** Consider two points the same if within ~0.5m */
function nearlySame([aLng, aLat]: LngLat, [bLng, bLat]: LngLat) {
  return Math.abs(aLng - bLng) < 1e-5 && Math.abs(aLat - bLat) < 1e-5;
}

export default function RoutePlanningPanel() {
  const { userLocation, stops, setStops, setWaypoints } = useRoute();

  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<"walking" | "driving" | "cycling">(
    "walking"
  );
  const [error, setError] = useState<string | null>(null);
  const [etaMin, setEtaMin] = useState<number | null>(null);
  const [distanceKm, setDistanceKm] = useState<number | null>(null);
  const [steps, setSteps] = useState<StepItem[]>([]);

  const uiStops: UiStop[] = useMemo(() => {
    const list: UiStop[] = [];
    if (userLocation) {
      list.push({
        kind: "origin",
        id: "origin",
        name: "Your location",
        disabled: true,
      });
    }
    for (const s of stops) {
      list.push({
        kind: "place",
        id: s.place_id,
        name: s.name || "",
        place: s,
      });
    }
    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userLocation, stops]);

  const updateStopName = (place_id: string, nextName: string) => {
    setStops(
      stops.map((p) => (p.place_id === place_id ? { ...p, name: nextName } : p))
    );
  };

  const addStop = () => {
    const id =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `tmp_${Date.now()}`;

    const newStop: PlaceStop = {
      place_id: id,
      name: "New stop",
      address: "",
      lat: 0,
      lng: 0,
      website_uri: null,
    };
    setStops([...stops, newStop]);
    // setActiveIndex(userLocation ? stops.length + 1 : stops.length);
  };

  /** Build the Mapbox-ready [lng, lat] list from context, validate coords */
  const buildPoints = (): LngLat[] => {
    const pts: LngLat[] = [];
    if (userLocation) pts.push([userLocation.longitude, userLocation.latitude]);

    for (const s of stops) {
      // ignore placeholders without coordinates
      if (
        typeof s.lng === "number" &&
        typeof s.lat === "number" &&
        !Number.isNaN(s.lng) &&
        !Number.isNaN(s.lat) &&
        !(s.lng === 0 && s.lat === 0)
      ) {
        const pt: LngLat = [s.lng, s.lat];
        // avoid duplicates if userLocation equals first stop etc.
        if (!pts.length || !nearlySame(pts[pts.length - 1], pt)) pts.push(pt);
      }
    }

    return pts;
  };

  /** Fetch directions, render list, and notify map via setWaypoints */
  const handleStart = async () => {
    setError(null);
    setSteps([]);
    setEtaMin(null);
    setDistanceKm(null);

    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === "YOUR_MAPBOX_TOKEN_HERE") {
      setError("Missing Mapbox token. Set NEXT_PUBLIC_MAPBOX_TOKEN.");
      return;
    }

    const points = buildPoints();

    if (points.length < 2) {
      setError(
        "Add at least a start and one destination with valid coordinates."
      );
      return;
    }

    setLoading(true);
    try {
      // Let the map know what to draw (if your map consumes waypoints)
      setWaypoints(points);

      const url = buildDirectionsUrl(profile, points);
      const res = await fetch(url);
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Directions error ${res.status}: ${txt}`);
      }
      const data = await res.json();

      const route = data?.routes?.[0];
      if (!route) {
        throw new Error("No route found for the provided points.");
      }

      // Gather instructions
      const legs = route.legs ?? [];
      const collected: StepItem[] = [];
      for (const leg of legs) {
        for (const step of leg.steps ?? []) {
          const instruction = step.maneuver?.instruction ?? "";
          // Parse instruction to separate main and sub parts
          // Look for common patterns like "Via [Street]" or "Continue to [Street]"
          let mainInstruction = instruction;
          let subInstruction = "";

          // Try to extract sub-instructions like "Turn left", "Turn right", "Continue straight"
          const turnPatterns = [
            /^(.*?)\s+(Turn left|Turn right|Continue straight|Go straight|Head|Keep left|Keep right)\.?\s*(.*)$/i,
            /^(Via .*?)\s+(Turn left|Turn right|Continue straight|Go straight|Head|Keep left|Keep right)\.?\s*(.*)$/i,
            /^(Continue to .*?)\s+(Turn left|Turn right|Continue straight|Go straight|Head|Keep left|Keep right)\.?\s*(.*)$/i,
          ];

          for (const pattern of turnPatterns) {
            const match = instruction.match(pattern);
            if (match) {
              mainInstruction = match[1].trim();
              subInstruction = `${match[2]}${
                match[3] ? " " + match[3] : ""
              }`.trim();
              break;
            }
          }

          // If no pattern matched, try simple sentence splitting
          if (!subInstruction) {
            const parts = instruction.split(". ");
            if (parts.length > 1) {
              mainInstruction = parts[0];
              subInstruction = parts.slice(1).join(". ");
            }
          }

          collected.push({
            text: instruction,
            distance: step.distance ?? 0,
            mainInstruction: mainInstruction,
            subInstruction: subInstruction,
          });
        }
      }
      setSteps(collected);

      // Set summary
      setEtaMin(Math.round((route.duration ?? 0) / 60));
      setDistanceKm((route.distance ?? 0) / 1000);
    } catch (e: unknown) {
      setError((e as Error)?.message || "Failed to fetch directions.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 max-h-[52vh] overflow-y-auto transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-800">Route Planner</h2>

        {/* Simple profile switcher */}
        <select
          className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white"
          value={profile}
          onChange={(e) =>
            setProfile(e.target.value as "walking" | "driving" | "cycling")
          }
        >
          <option value="walking">Walking</option>
          <option value="driving">Driving</option>
          <option value="cycling">Cycling</option>
        </select>
      </div>

      {/* Route Line with Stops */}
      <div className="relative mb-8">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-green-500"></div>

        {uiStops.map((s, idx) => (
          <div key={s.id} className="relative flex items-start mb-6 group">
            {/* Node */}
            <div className="w-4 h-4 rounded-full border-2 flex-shrink-0 mt-2 z-10 bg-white border-gray-300" />

            {/* Input */}
            <div className="ml-5 flex-1">
              <input
                type="text"
                value={s.name}
                disabled={true}
                readOnly={true}
                className="w-full px-4 py-3 rounded-lg border text-sm bg-gray-100 text-gray-700 border-gray-200 cursor-default"
                placeholder={
                  s.kind === "origin" ? "Your location" : "Destination"
                }
              />
              {s.kind === "place" && s.place.address ? (
                <p className="text-xs text-gray-500 mt-2">{s.place.address}</p>
              ) : null}
            </div>
          </div>
        ))}

        {/* Add Stop Button */}
        <div className="relative flex items-center mt-2">
          <div className="w-4 h-4 rounded-full border-2 border-dashed border-gray-300"></div>
          <button
            onClick={addStop}
            className="ml-4 flex items-center text-sm font-medium text-gray-600 hover:text-green-600 transition-colors"
          >
            <Plus size={16} className="mr-1" />
            Add stop
          </button>
        </div>
      </div>

      {/* Start Button */}
      <div className="flex justify-center">
        <button
          onClick={handleStart}
          disabled={loading}
          className="bg-green-500 text-white px-8 py-3 rounded-xl text-sm font-semibold hover:bg-green-600 active:scale-95 transition-all flex items-center shadow-md disabled:opacity-70"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="mr-2 animate-spin" />
              Calculating…
            </>
          ) : (
            <>
              <Play size={18} className="mr-2" />
              Start
            </>
          )}
        </button>
      </div>

      {/* Directions Panel — appears UNDER the Start button */}
      <div className="mt-6">
        {error ? (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </div>
        ) : null}

        {/* Route Summary - Duration and Distance */}
        {etaMin != null && distanceKm != null ? (
          <div className="border-t border-gray-200 pt-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="text-lg font-bold text-gray-800">
                {etaMin >= 60
                  ? `${Math.floor(etaMin / 60)}hr ${etaMin % 60} min`
                  : `${etaMin} min`}
              </div>
              <div className="text-sm text-gray-600">
                {distanceKm.toFixed(1)} km
              </div>
            </div>
          </div>
        ) : null}

        {/* Directions List */}
        {steps.length > 0 ? (
          <div className="space-y-0">
            {steps.map((s, i) => (
              <div key={i} className="border-b border-gray-100 last:border-b-0">
                <div className="py-3">
                  <div className="text-sm font-medium text-gray-800 mb-1">
                    {s.mainInstruction}
                  </div>
                  {s.subInstruction && (
                    <div className="text-xs text-gray-500">
                      {s.subInstruction}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-500">
            Turn-by-turn directions will appear here after you press{" "}
            <span className="font-medium">Start</span>.
          </p>
        )}
      </div>
    </div>
  );
}
