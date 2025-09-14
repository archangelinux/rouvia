'use client';

import { useState } from 'react';
import { Home, Plus, LogOut, X } from 'lucide-react';
import ProfileDetails from './ProfileDetails';

export default function UserProfile() {
  const [isOpen, setIsOpen] = useState(false);
  const [showProfileDetails, setShowProfileDetails] = useState(false);

  // Show ProfileDetails page if requested
  if (showProfileDetails) {
    return <ProfileDetails onClose={() => setShowProfileDetails(false)} />;
  }

  return (
    <div className="relative">
      {/* Profile Circle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-lg font-semibold shadow-lg hover:shadow-xl transition-shadow duration-200 cursor-pointer"
      >
        🍊
      </button>

      {/* Popup Menu */}
      {isOpen && (
        <div className="absolute top-0 right-0 -mt-2 w-80 bg-gray-100 rounded-2xl shadow-xl border border-gray-200 z-20 p-6">
          {/* Header */}
          <div className="space-y-4">
            {/* Email and Close Button */}
            <div className="flex items-center justify-center relative">
              <span className="text-sm text-gray-600 font-medium">jackrussel@gmail.com</span>
              <button 
                onClick={() => setIsOpen(false)}
                className="absolute right-0 text-black hover:text-gray-700 transition-colors"
              >
                <X size={16} />
              </button>
            </div>
            
            {/* Profile Section */}
            <div className="flex flex-col items-center space-y-3">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-2xl font-semibold">
                🍊
              </div>
              <h3 className="text-lg font-bold text-black">Hi, Jack!</h3>
            </div>
          </div>

          {/* Menu Items */}
          <div className="space-y-3 mt-4">
            {/* Profile Details Card */}
            <button 
              onClick={() => {
                setShowProfileDetails(true);
                setIsOpen(false);
              }}
              className="w-full text-left bg-white rounded-2xl px-6 py-5 flex items-center space-x-4 transition-colors duration-150"
            >
              <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
                <Home size={20} className="text-white" />
              </div>
              <span className="font-semibold text-black">Profile Details</span>
            </button>
            
            {/* Add another account */}
            <button className="w-full text-left bg-white rounded-2xl px-6 py-4 flex items-center space-x-4 transition-colors duration-150">
              <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                <Plus size={16} className="text-white" />
              </div>
              <span className="font-medium text-black">Add another account</span>
            </button>
            
            {/* Sign out */}
            <button className="w-full text-left bg-white rounded-2xl px-6 py-4 flex items-center space-x-4 transition-colors duration-150">
              <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                <LogOut size={16} className="text-white" />
              </div>
              <span className="font-medium text-black">Sign out</span>
            </button>
          </div>
        </div>
      )}

      {/* Backdrop to close popup */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-10" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
