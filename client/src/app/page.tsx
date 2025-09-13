"use client";

import { useState } from "react";
import Map from "@/components/map";
import Chatbox from "@/components/chat";

export default function Home() {
  const [chatOpen, setChatOpen] = useState(true);

  return (
    <div className="relative w-screen h-screen">
      {/* Map full screen */}
      <Map />

      {/* Floating chatbox */}
      <div className="absolute top-4 left-4 z-10">
        <Chatbox open={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />
      </div>
    </div>
  );
}