'use client';

import { ShoppingCart, Shirt, MapPin } from 'lucide-react';

interface MarkerProps {
  name: string;
  type: 'store' | 'clothing' | 'location';
  className?: string;
}

export function StoreMarker({ className = '' }: Omit<MarkerProps, 'name'>) {
  return (
    <div className={`bg-white rounded-full border-2 border-blue-500 flex items-center justify-center shadow-lg ${className}`}>
      <ShoppingCart size={16} className="text-black" />
    </div>
  );
}

export function ClothingMarker({ className = '' }: Omit<MarkerProps, 'name'>) {
  return (
    <div className={`bg-white rounded-full border-2 border-blue-500 flex items-center justify-center shadow-lg ${className}`}>
      <Shirt size={16} className="text-black" />
    </div>
  );
}

export function LocationMarker({ className = '' }: Omit<MarkerProps, 'name'>) {
  return (
    <div className={`bg-white rounded-full border-2 border-green-500 flex items-center justify-center shadow-lg ${className}`}>
      <MapPin size={16} className="text-black" />
    </div>
  );
}
