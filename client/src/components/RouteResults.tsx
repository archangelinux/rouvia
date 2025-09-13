'use client';

import { Map } from 'lucide-react';

export default function RouteResults() {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 min-h-40">
      {/* Empty state for now */}
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center space-y-3">
          <Map size={32} className="mx-auto text-gray-400" />
          <p className="text-sm text-gray-500">Route results will appear here</p>
        </div>
      </div>
    </div>
  );
}
