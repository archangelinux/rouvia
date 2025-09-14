'use client';

import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';

export default function LandingPage() {
  const { login } = useAuth();
  return (
    <div className="min-h-screen relative">
      {/* Background placeholder */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-100"></div>
      
      {/* Left green edge */}
      <div className="absolute left-0 top-8 bottom-0 w-16 bg-green-500 rounded-r-full opacity-20"></div>
      
      {/* Right green edge */}
      <div className="absolute right-0 top-8 bottom-0 w-16 bg-green-500 rounded-l-full opacity-20"></div>
      
      {/* Hero Section */}
      <div className="min-h-[80vh] flex items-center justify-center py-12 relative z-10">
        <div className="max-w-4xl w-full mx-4 relative z-10">
          <div className="flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
            
            {/* Left Side - Logo and Content */}
            <div className="flex-1 text-center lg:text-left space-y-8">
              {/* Logo */}
              <div className="flex justify-center lg:justify-start">
                <div className="w-55 h-55 relative mb-[-50]">
                  <Image
                    src="/logo.png"
                    alt="Rouvia Logo"
                    width={120}
                    height={120}
                    className="w-full h-full object-contain drop-shadow-xl"
                    priority
                  />
                </div>
              </div>

              {/* Title */}
              <div className= "mt-[-50px]">
                <h1 className="text-3xl lg:text-4xl font-bold text-gray-600 mb-6">
                  You can go anywhere.
                </h1>
                <p className="text-gray-700 text-base lg:text-lg leading-relaxed max-w-lg mx-auto lg:mx-0">
                  An AI-powered driving companion that optimizes your route and curates sidequests. 
                  Get where you need to go, and discover where you didn&apos;t know you wanted to.
                </p>
              </div>

              {/* Features */}
              <div className="space-y-5 max-w-lg mx-auto lg:mx-0">
                <div className="flex items-start text-gray-800">
                  <div className="w-4 h-4 bg-emerald-400 rounded-full mr-4 mt-1 flex-shrink-0 shadow-lg animate-pulse" 
                       style={{boxShadow: '0 0 20px rgba(52, 211, 153, 0.4)'}}></div>
                  <span className="text-sm font-medium">Voice-powered navigation for hands-free driving</span>
                </div>
                <div className="flex items-start text-gray-800">
                  <div className="w-4 h-4 bg-sky-400 rounded-full mr-4 mt-1 flex-shrink-0 shadow-lg animate-pulse" 
                       style={{boxShadow: '0 0 20px rgba(56, 189, 248, 0.4)', animationDelay: '0.5s'}}></div>
                  <span className="text-sm font-medium">Smart route optimization and trends discovery</span>
                </div>
                <div className="flex items-start text-gray-800">
                  <div className="w-4 h-4 bg-violet-400 rounded-full mr-4 mt-1 flex-shrink-0 shadow-lg animate-pulse" 
                       style={{boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)', animationDelay: '1s'}}></div>
                  <span className="text-sm font-medium">Personalized recommendations and commands</span>
                </div>
              </div>

              {/* Login Button */}
              <div className="flex justify-center lg:justify-start">
                <div className="text-center lg:text-left">
                  <button
                    onClick={() => login()}
                    className="inline-block bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-semibold px-8 py-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-green-500/25 hover:scale-105 text-base"
                  >
                    Get Started
                  </button>
                  <p className="text-gray-600 text-xs mt-5 font-medium">
                    Sign in to start planning your perfect route
                  </p>
                </div>
              </div>
            </div>

            {/* Right Side - Hero Image */}
            <div className="flex-1 flex justify-center lg:justify-end">
              <div className="w-80 max-w-sm">
                <div className="relative">
                  <Image
                    src="/hero-image-2.png"
                    alt="Rouvia Hero Image"
                    width={150}
                    height={225}
                    className="w-full h-auto object-contain drop-shadow-2xl"
                    priority
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Screenshots Section */}
      <div className="w-full px-4 py-16 relative z-10 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Helping you get the most of your city.</h2>
            <p className="text-gray-600 text-lg">Made for the curious, and the busy.</p>
          </div>
          <div className="space-y-8">
            {/* Screenshot 1 - Full width */}
            <div className="flex justify-center">
              <div className="w-full max-w-2xl">
                <div className="relative rounded-xl overflow-hidden shadow-2xl hover:shadow-3xl transition-shadow duration-300">
                  <Image
                    src="/screenshot-1.png"
                    alt="Rouvia Screenshot 1 - Voice Navigation Interface"
                    width={800}
                    height={600}
                    className="w-full h-auto object-cover hover:scale-105 transition-transform duration-300"
                  />
                </div>
              </div>
            </div>
            
            {/* Screenshots 2 & 3 - Combined width same as first */}
            <div className="flex justify-center gap-6 md:gap-8 max-w-2xl mx-auto">
              {/* Screenshot 2 */}
              <div className="flex-1">
                <div className="relative rounded-xl overflow-hidden shadow-2xl hover:shadow-3xl transition-shadow duration-300">
                  <Image
                    src="/screenshot-2.png"
                    alt="Rouvia Screenshot 2 - Route Planning"
                    width={400}
                    height={600}
                    className="w-full h-auto object-cover hover:scale-105 transition-transform duration-300"
                  />
                </div>
              </div>
              
              {/* Screenshot 3 */}
              <div className="flex-1">
                <div className="relative rounded-xl overflow-hidden shadow-2xl hover:shadow-3xl transition-shadow duration-300">
                  <Image
                    src="/screenshot-3.png"
                    alt="Rouvia Screenshot 3 - Sidequest Discovery"
                    width={400}
                    height={600}
                    className="w-full h-auto object-cover hover:scale-105 transition-transform duration-300"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="w-full py-8 bg-gray-50 border-t border-gray-200 relative z-10">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-gray-600 text-sm">
            © 2025 Made with ❤️ at Hack the North
          </p>
        </div>
      </footer>
    </div>
  );
}
