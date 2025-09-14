"use client";

import React, { useState } from "react";
import Image from "next/image";
import MapboxMap from "@/components/MapboxMap";
import UserProfile from "@/components/UserProfile";
import ChatInterface from "@/components/ChatInterface";
import RoutePlanningPanel from "@/components/RoutePlanningPanel";
import { RouteProvider } from "@/components/context/route-context"; // ✅ import your context provider

export default function Home() {
  const [chatOpen, setChatOpen] = useState(true);

  return (
    <RouteProvider>
      <div className="relative w-full h-screen overflow-hidden">
        {/* Mapbox Map - Full Background */}
        <MapboxMap />

        {/* Top Right - Logo and User Profile */}
        <div className="absolute top-6 right-6 z-20 flex items-center space-x-2">
          <Image
            src="/logo.png"
            alt="Rouvia Logo"
            width={90}
            height={50}
            className="object-contain"
          />
          <UserProfile />
        </div>

        {/* Left Side - Route Planning Panel */}
        <div className="absolute top-6 left-6 z-10 w-96">
          <RoutePlanningPanel />
        </div>

        {/* Left Side - Chat Interface */}
        {chatOpen && (
          <div className="absolute bottom-6 left-6 z-10 w-96">
            <ChatInterface />
          </div>
        )}
      </div>
    </RouteProvider>
  );
}
