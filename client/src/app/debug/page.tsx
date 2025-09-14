"use client";

import { useSession } from 'next-auth/react';

export default function DebugPage() {
  const { data: session, status } = useSession();

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Auth Debug</h1>
      <div className="space-y-4">
        <div>
          <strong>Status:</strong> {status}
        </div>
        <div>
          <strong>User:</strong> {session?.user ? 'Authenticated' : 'Not authenticated'}
        </div>
        {session?.user && (
          <div>
            <strong>User Data:</strong>
            <pre className="bg-gray-100 p-4 rounded mt-2">
              {JSON.stringify(session.user, null, 2)}
            </pre>
          </div>
        )}
        {session && (
          <div>
            <strong>Session Data:</strong>
            <pre className="bg-gray-100 p-4 rounded mt-2">
              {JSON.stringify(session, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
