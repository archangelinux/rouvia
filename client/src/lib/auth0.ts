// Simple Auth0 integration without NextAuth
import { createAuth0Client } from '@auth0/auth0-spa-js';

// Check if Auth0 is properly configured
export const isAuth0Configured = () => {
  return !!(process.env.NEXT_PUBLIC_AUTH0_DOMAIN && process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID);
};

const auth0Config = {
  domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN || 'dummy.auth0.com',
  clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || 'dummy-client-id',
  authorizationParams: {
    redirect_uri: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
  },
  // Suppress development key warnings
  useRefreshTokens: true,
  cacheLocation: 'localstorage' as const,
  // Hide Auth0 development warnings
  advancedOptions: {
    defaultScope: 'openid profile email',
  },
  // Suppress console warnings
  skipRedirectCallback: false,
};

let auth0Client: any = null;

export const initAuth0 = async (forceRecreate = false) => {
  if (typeof window === 'undefined') return null;
  
  // If Auth0 is not configured, return null to avoid warnings
  if (!isAuth0Configured()) {
    console.log('Auth0 not configured - skipping initialization');
    return null;
  }
  
  if (!auth0Client || forceRecreate) {
    if (forceRecreate && auth0Client) {
      // Clear the old client
      auth0Client = null;
    }
    
    // Suppress Auth0 development warnings
    const originalConsoleWarn = console.warn;
    console.warn = (...args) => {
      const message = args[0];
      if (typeof message === 'string' && message.includes('development keys')) {
        // Suppress Auth0 development key warnings
        return;
      }
      originalConsoleWarn.apply(console, args);
    };
    
    try {
      auth0Client = await createAuth0Client(auth0Config);
    } finally {
      // Restore original console.warn
      console.warn = originalConsoleWarn;
    }
  }
  return auth0Client;
};

export const login = async (forceLogin = false) => {
  if (!isAuth0Configured()) {
    console.log('Auth0 not configured - login disabled');
    return;
  }
  
  const client = await initAuth0();
  if (client) {
    await client.loginWithRedirect({
      authorizationParams: {
        prompt: forceLogin ? 'login' : undefined, // Force login screen if requested
      },
    });
  }
};

export const logout = async () => {
  if (!isAuth0Configured()) {
    console.log('Auth0 not configured - logout disabled');
    return;
  }
  
  const client = await initAuth0();
  if (client) {
    await client.logout({
      logoutParams: {
        returnTo: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
      },
      federated: true, // This ensures logout from all connected providers (Google, etc.)
    });
    // Clear the client after logout to force recreation on next login
    auth0Client = null;
  }
};

export const getUser = async () => {
  if (!isAuth0Configured()) {
    return null;
  }
  
  const client = await initAuth0();
  if (client) {
    return await client.getUser();
  }
  return null;
};

export const isAuthenticated = async () => {
  if (!isAuth0Configured()) {
    return false;
  }
  
  const client = await initAuth0();
  if (client) {
    return await client.isAuthenticated();
  }
  return false;
};
