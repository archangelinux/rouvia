'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Plus, LogOut, X, User } from 'lucide-react';
import Image from 'next/image';
import ProfileDetails from './ProfileDetails';

export default function UserProfile() {
  const [isOpen, setIsOpen] = useState(false);
  const [showProfileDetails, setShowProfileDetails] = useState(false);
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="w-10 h-10 rounded-full bg-gray-300 animate-pulse"></div>
    );
  }

  if (!user) {
    return null;
  }

  // Show ProfileDetails page if requested
  if (showProfileDetails) {
    return <ProfileDetails onClose={() => setShowProfileDetails(false)} user={user} />;
  }

  return (
    <div className="relative">
      {/* Profile Circle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-10 h-10 rounded-full bg-slate-600 flex items-center justify-center text-white text-sm font-medium shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer overflow-hidden border border-slate-500"
      >
        {(user as { picture?: string }).picture ? (
          <Image 
            src={(user as { picture?: string }).picture!} 
            alt={user.name || 'User'} 
            width={40}
            height={40}
            className="w-full h-full rounded-full object-cover" 
          />
        ) : (
          user.name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase() || '🍊'
        )}
      </button>

      {/* Popup Menu */}
      {isOpen && (
        <div className="absolute top-0 right-0 -mt-2 w-80 bg-gray-100 rounded-2xl shadow-xl border border-gray-200 z-20 p-6">
          {/* Header */}
          <div className="space-y-4">
            {/* Email and Close Button */}
            <div className="flex items-center justify-center relative">
              <span className="text-sm text-gray-600 font-medium truncate max-w-[200px]">
                {user.email}
              </span>
              <button 
                onClick={() => setIsOpen(false)}
                className="absolute right-0 text-black hover:text-gray-700 transition-colors cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>
            
            {/* Profile Section */}
            <div className="flex flex-col items-center space-y-3">
              <div className="w-16 h-16 rounded-full bg-slate-600 flex items-center justify-center text-white text-xl font-medium overflow-hidden border border-slate-500 shadow-md">
                {(user as { picture?: string }).picture ? (
                  <Image 
                    src={(user as { picture?: string }).picture!} 
                    alt={user.name || 'User'} 
                    width={64}
                    height={64}
                    className="w-full h-full rounded-full object-cover" 
                  />
                ) : (
                  user.name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase() || '🍊'
                )}
              </div>
              <h3 className="text-lg font-bold text-black">
                Hi, {user.name?.split(' ')[0] || user.email?.split('@')[0] || 'User'}!
              </h3>
            </div>
          </div>

          {/* Menu Items */}
          <div className="space-y-3 mt-4">
            {/* Profile Details Card */}
            <button 
              onClick={() => {
                setIsOpen(false);
                setShowProfileDetails(true);
              }}
              className="w-full text-left bg-white rounded-2xl px-6 py-5 flex items-center space-x-4 transition-colors duration-150 hover:bg-gray-50 cursor-pointer"
            >
              <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
                <User size={20} className="text-white" />
              </div>
              <span className="font-semibold text-black">Profile Details</span>
            </button>
            
            {/* Add another account */}
            <button className="w-full text-left bg-white rounded-2xl px-6 py-4 flex items-center space-x-4 transition-colors duration-150 hover:bg-gray-50 cursor-pointer">
              <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                <Plus size={16} className="text-white" />
              </div>
              <span className="font-medium text-black">Add another account</span>
            </button>
            
            {/* Sign out */}
            <button 
              onClick={async () => {
                try {
                  console.log('Signing out...');
                  await logout();
                  window.location.href = '/landing';
                } catch (error) {
                  console.error('Sign out error:', error);
                  // Fallback: clear storage and redirect
                  localStorage.clear();
                  sessionStorage.clear();
                  window.location.href = '/landing';
                }
              }}
              className="w-full text-left bg-white rounded-2xl px-6 py-4 flex items-center space-x-4 transition-colors duration-150 hover:bg-gray-50 cursor-pointer"
            >
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
          className="fixed inset-0 z-10 cursor-pointer" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
