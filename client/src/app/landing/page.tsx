'use client';

import Image from 'next/image';
import { signIn } from 'next-auth/react';

export default function LandingPage() {

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center relative overflow-hidden">
      {/* Cityscape Background */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-800/50 via-transparent to-transparent"></div>
      
      {/* Animated cityscape silhouette */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-700 to-transparent">
        <div className="flex justify-between items-end h-full px-4">
          <div className="w-8 h-20 bg-slate-600 rounded-t"></div>
          <div className="w-6 h-16 bg-slate-600 rounded-t"></div>
          <div className="w-10 h-24 bg-slate-600 rounded-t"></div>
          <div className="w-7 h-18 bg-slate-600 rounded-t"></div>
          <div className="w-5 h-14 bg-slate-600 rounded-t"></div>
          <div className="w-9 h-22 bg-slate-600 rounded-t"></div>
          <div className="w-6 h-16 bg-slate-600 rounded-t"></div>
          <div className="w-8 h-20 bg-slate-600 rounded-t"></div>
          <div className="w-4 h-12 bg-slate-600 rounded-t"></div>
          <div className="w-7 h-18 bg-slate-600 rounded-t"></div>
        </div>
      </div>

      {/* Floating map elements */}
      <div className="absolute top-20 left-10 w-16 h-16 bg-blue-500/20 rounded-full animate-pulse"></div>
      <div className="absolute top-40 right-20 w-12 h-12 bg-green-500/20 rounded-full animate-pulse delay-1000"></div>
      <div className="absolute bottom-40 left-20 w-20 h-20 bg-purple-500/20 rounded-full animate-pulse delay-2000"></div>

      <div className="max-w-md w-full mx-4 relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-24 h-24 mx-auto mb-6 relative">
            <Image
              src="/logo.png"
              alt="Rouvia Logo"
              width={96}
              height={96}
              className="w-full h-full object-contain"
              priority
            />
          </div>
          <h1 className="text-5xl font-bold text-white mb-3 tracking-tight">Rouvia</h1>
          <p className="text-blue-200 text-lg font-medium">Smart Route Planning</p>
        </div>

        {/* Description */}
        <div className="bg-white/10 backdrop-blur-md rounded-3xl p-8 mb-8 border border-white/20">
          <h2 className="text-2xl font-bold text-white mb-4">Welcome to Rouvia</h2>
          <p className="text-blue-100 leading-relaxed text-lg">
            Your AI-powered navigation assistant for hands-free driving. 
            Plan routes, discover places, and navigate with voice commands.
          </p>
        </div>

        {/* Features */}
        <div className="space-y-4 mb-8">
          <div className="flex items-center text-white">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-4"></div>
            <span className="text-lg">Voice-powered navigation</span>
          </div>
          <div className="flex items-center text-white">
            <div className="w-3 h-3 bg-blue-400 rounded-full mr-4"></div>
            <span className="text-lg">Smart route optimization</span>
          </div>
          <div className="flex items-center text-white">
            <div className="w-3 h-3 bg-purple-400 rounded-full mr-4"></div>
            <span className="text-lg">Personalized recommendations</span>
          </div>
        </div>

        {/* Login Button */}
        <div className="text-center">
          <button
            onClick={() => signIn('auth0', { callbackUrl: '/' })}
            className="inline-block bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold px-10 py-5 rounded-2xl transition-all duration-300 shadow-2xl hover:shadow-green-500/25 hover:scale-105 text-lg"
          >
            Get Started
          </button>
          <p className="text-blue-200 text-sm mt-6 font-medium">
            Sign in to start planning your perfect route
          </p>
        </div>
      </div>

      {/* Subtle grid pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="h-full w-full" style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }}></div>
      </div>
    </div>
  );
}
