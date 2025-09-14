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
        <div className="absolute top-0 right-0 -mt-2 w-72 bg-gray-50 rounded-2xl shadow-xl border border-gray-200 z-20 p-5">
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
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-xl font-semibold">
                🍊
              </div>
              <h3 className="text-base font-bold text-black">Hi, Jack!</h3>
            </div>
          </div>

          {/* Menu Items */}
          <div className="space-y-2 mt-5">
            {/* Profile Details Card */}
            <button 
              onClick={() => {
                setShowProfileDetails(true);
                setIsOpen(false);
              }}
              className="w-full text-center bg-white rounded-xl px-4 py-4 flex flex-col items-center space-y-2 transition-colors duration-150 hover:bg-gray-50"
            >
              <div className="w-10 h-10 rounded-full bg-green-300 flex items-center justify-center">
                <Home size={18} className="text-green-700" />
              </div>
              <span className="text-sm font-medium text-black">Profile Details</span>
            </button>
            
            {/* Add another account */}
            <button className="w-full text-center bg-white rounded-xl px-4 py-3 flex flex-col items-center space-y-2 transition-colors duration-150 hover:bg-gray-50">
              <div className="w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center">
                <Plus size={14} className="text-white" />
              </div>
              <span className="text-sm font-medium text-black">Add another account</span>
            </button>
            
            {/* Sign out */}
            <button className="w-full text-center bg-white rounded-xl px-4 py-3 flex flex-col items-center space-y-2 transition-colors duration-150 hover:bg-gray-50">
              <div className="w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center">
                <LogOut size={14} className="text-white" />
              </div>
              <span className="text-sm font-medium text-black">Sign out</span>
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
