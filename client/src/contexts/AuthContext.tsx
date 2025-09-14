'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { initAuth0, login, logout, getUser, isAuthenticated } from '@/lib/auth0';

interface User {
  sub: string;
  email: string;
  name: string;
  picture?: string;
  nickname?: string;
  given_name?: string;
  family_name?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Initialize Auth0 client first
        const client = await initAuth0();
        if (!client) {
          console.log('Auth0 client not initialized');
          setIsLoading(false);
          return;
        }

        // Handle Auth0 callback if we have URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('code') && urlParams.get('state')) {
          console.log('Handling Auth0 callback...');
          try {
            await client.handleRedirectCallback();
            console.log('Auth0 callback handled successfully');
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
          } catch (error) {
            console.error('Error handling Auth0 callback:', error);
          }
        }

        // Check authentication status
        const authenticated = await client.isAuthenticated();
        console.log('Auth0 authenticated:', authenticated);
        
        if (authenticated) {
          const userData = await client.getUser();
          console.log('Auth0 user data:', userData);
          
          if (userData) {
            setUser(userData);
            
            // Create user profile in MongoDB
            try {
              const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
              console.log('Attempting to create user profile via:', `${apiUrl}/api/user-profile/create-or-update`);
              
              const response = await fetch(`${apiUrl}/api/user-profile/create-or-update`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  auth0_user_id: userData.sub,
                  email: userData.email,
                  name: userData.name,
                  nickname: userData.nickname,
                  picture: userData.picture,
                  given_name: userData.given_name,
                  family_name: userData.family_name,
                }),
              });

              if (!response.ok) {
                const errorText = await response.text();
                console.error('Failed to create/update user profile:', response.status, errorText);
              } else {
                console.log('User profile created/updated successfully');
              }
            } catch (error) {
              console.error('Error creating/updating user profile:', error);
              console.log('This is not critical - user can still use the app');
            }
          }
        }
      } catch (error) {
        console.error('Auth check error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = async () => {
    try {
      console.log('🔄 Starting fresh login process...');
      // Force recreate Auth0 client for fresh login
      await initAuth0(true);
      console.log('✅ Auth0 client recreated');
      // Force login screen to show (prompt=login)
      await login(true);
      console.log('✅ Login redirect initiated with forced login screen');
    } catch (error) {
      console.error('❌ Login error:', error);
    }
  };

  const handleLogout = async () => {
    try {
      console.log('🔄 Starting logout process...');
      // Clear local state first
      setUser(null);
      console.log('✅ Local state cleared');
      
      const client = await initAuth0();
      if (client) {
        console.log('✅ Auth0 client found, logging out with federated logout...');
        await client.logout({
          logoutParams: {
            returnTo: window.location.origin + '/landing',
          },
          federated: true, // Logout from Google and all other providers
        });
        console.log('✅ Auth0 federated logout completed');
        // The logout function in auth0.ts will clear the client
      } else {
        console.log('⚠️ No Auth0 client, redirecting to landing...');
        // If no client, just redirect to landing
        window.location.href = '/landing';
      }
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Fallback: clear local state and redirect
      setUser(null);
      window.location.href = '/landing';
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login: handleLogin,
      logout: handleLogout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
