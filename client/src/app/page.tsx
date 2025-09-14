"use client";

import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Image from "next/image";
import MapboxMap from "@/components/MapboxMap";
import UserProfile from "@/components/UserProfile";
import ChatInterface from "@/components/ChatInterface";
import RoutePlanningPanel from "@/components/RoutePlanningPanel";
import { RouteProvider } from "@/components/context/route-context";

export default function Home() {
  const chatOpen = true; // Chat is always open for now
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    console.log('=== AUTH DEBUG ===');
    console.log('User exists:', !!user);
    console.log('Is loading:', isLoading);
    console.log('Is authenticated:', isAuthenticated);
    console.log('User:', user);
    console.log('URL:', window.location.href);
    
    // Only redirect if we're not loading and definitely not authenticated
    if (!isLoading && !user) {
      console.log('🚀 REDIRECTING TO LANDING PAGE - not authenticated');
      router.push('/landing');
    } else if (user) {
      console.log('✅ User authenticated:', user);
    } else {
      console.log('⏳ Still loading...');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-gray-600 text-xl">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to landing page
  }

  // Extract user ID for passing to components
  const userSub = user.sub || user.id || null;

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
            <ChatInterface userSub={userSub} />
          </div>
        )}
      </div>
    </RouteProvider>
  );
}
