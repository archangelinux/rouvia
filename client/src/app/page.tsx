"use client";

import React, { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Image from "next/image";
import MapboxMap from "@/components/MapboxMap";
import UserProfile from "@/components/UserProfile";
import ChatInterface from "@/components/ChatInterface";
import RoutePlanningPanel from "@/components/RoutePlanningPanel";
import { RouteProvider } from "@/components/context/route-context";

export default function Home() {
  const [chatOpen, setChatOpen] = useState(true);
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    console.log('=== AUTH DEBUG ===');
    console.log('Session exists:', !!session);
    console.log('Status:', status);
    console.log('User:', session?.user);
    console.log('URL search params:', window.location.search);
    console.log('Has callbackUrl:', window.location.search.includes('callbackUrl'));
    
    // Redirect to landing page if not authenticated
    if (status === 'unauthenticated' && !window.location.search.includes('callbackUrl')) {
      console.log('🚀 REDIRECTING TO LANDING PAGE - not authenticated');
      router.push('/landing');
    } else if (session) {
      console.log('✅ User authenticated:', session.user);
    } else {
      console.log('⏳ Still loading or other state...');
    }
  }, [session, status, router]);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-gray-600 text-xl">Loading...</div>
      </div>
    );
  }

  if (!session) {
    return null; // Will redirect to landing page
  }

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
