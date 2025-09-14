"use client";

import { useMemo, useState } from "react";
import { Play, Plus } from "lucide-react";
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

export default function RoutePlanningPanel() {
  const { userLocation, stops, setStops } = useRoute();
  const [activeIndex, setActiveIndex] = useState<number>(1);

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
    if (activeIndex >= list.length) {
      setActiveIndex(Math.max(0, list.length - 1));
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
    setActiveIndex(userLocation ? stops.length + 1 : stops.length);
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 max-h-[60vh] overflow-y-auto transition-all">
      {/* Header */}
      <h2 className="text-lg font-semibold text-gray-800 mb-6">
        Route Planner
      </h2>

      {/* Route Line with Stops */}
      <div className="relative mb-8">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-green-500"></div>

        {uiStops.map((s, idx) => (
          <div
            key={s.id}
            className="relative flex items-start mb-6 cursor-pointer group"
            onClick={() => setActiveIndex(idx)}
          >
            {/* Node */}
            <div
              className={[
                "w-4 h-4 rounded-full border-2 flex-shrink-0 mt-2 z-10 transition-colors",
                idx === activeIndex
                  ? "bg-green-500 border-green-500"
                  : "bg-white border-gray-300 group-hover:border-green-400",
              ].join(" ")}
            />

            {/* Input */}
            <div className="ml-5 flex-1">
              <input
                type="text"
                value={s.name}
                disabled={s.kind === "origin"}
                onChange={(e) => {
                  if (s.kind === "place") updateStopName(s.id, e.target.value);
                }}
                className={[
                  "w-full px-4 py-3 rounded-lg border text-sm transition-colors",
                  s.kind === "origin"
                    ? "bg-gray-100 text-gray-500 border-gray-200"
                    : "bg-white border-gray-300 focus:border-green-500 focus:ring-2 focus:ring-green-200",
                ].join(" ")}
                placeholder={
                  s.kind === "origin" ? "Your location" : "Enter destination"
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
        <button className="bg-green-500 text-white px-8 py-3 rounded-xl text-sm font-semibold hover:bg-green-600 active:scale-95 transition-all flex items-center shadow-md">
          <Play size={18} className="mr-2" />
          Start
        </button>
      </div>
    </div>
  );
}
