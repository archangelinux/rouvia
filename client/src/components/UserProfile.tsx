'use client';

import { useState } from 'react';
import { Settings, Plus, LogOut, X } from 'lucide-react';

export default function UserProfile() {
  const [isOpen, setIsOpen] = useState(false);

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
        <div className="absolute top-0 right-0 -mt-2 w-80 bg-white rounded-2xl shadow-xl border border-gray-200 z-20 p-6">
          {/* Header */}
          <div className="space-y-4">
            {/* Email and Close Button */}
            <div className="flex items-center justify-center relative">
              <span className="text-sm text-gray-600 font-medium">jackrussel@gmail.com</span>
              <button 
                onClick={() => setIsOpen(false)}
                className="absolute right-0 text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X size={16} />
              </button>
            </div>
            
            {/* Profile Section */}
            <div className="flex flex-col items-center space-y-3">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-2xl font-semibold">
                🍊
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Hi, Jack!</h3>
            </div>
          </div>

          {/* Menu Items */}
          <div className="space-y-3 mt-4">
            <button className="w-full text-left text-lg text-gray-700 hover:bg-gray-100 rounded-xl px-6 py-5 flex items-center space-x-4 transition-colors duration-150 bg-gray-50">
              <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center">
                <Settings size={20} className="text-white" />
              </div>
              <span className="font-semibold">Profile Details</span>
            </button>
            
            <button className="w-full text-left text-sm text-gray-700 hover:bg-gray-100 rounded-lg px-8 py-3 flex items-center space-x-3 transition-colors duration-150">
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center">
                <Plus size={16} className="text-white" />
              </div>
              <span className="font-medium">Add another account</span>
            </button>
            
            <button className="w-full text-left text-sm text-gray-700 hover:bg-gray-100 rounded-lg px-8 py-3 flex items-center space-x-3 transition-colors duration-150">
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center">
                <LogOut size={16} className="text-white" />
              </div>
              <span className="font-medium">Sign out</span>
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
