// Debug file to check environment variables
export function debugAuth() {
  console.log('=== AUTH DEBUG ===');
  console.log('AUTH0_CLIENT_ID:', process.env.AUTH0_CLIENT_ID ? 'SET' : 'NOT SET');
  console.log('AUTH0_CLIENT_SECRET:', process.env.AUTH0_CLIENT_SECRET ? 'SET' : 'NOT SET');
  console.log('AUTH0_DOMAIN:', process.env.AUTH0_DOMAIN ? 'SET' : 'NOT SET');
  console.log('NEXTAUTH_SECRET:', process.env.NEXTAUTH_SECRET ? 'SET' : 'NOT SET');
  console.log('NEXTAUTH_URL:', process.env.NEXTAUTH_URL ? 'SET' : 'NOT SET');
  console.log('==================');
  
  if (!process.env.AUTH0_CLIENT_ID || !process.env.AUTH0_CLIENT_SECRET || !process.env.AUTH0_DOMAIN) {
    throw new Error('Missing required Auth0 environment variables');
  }
}
