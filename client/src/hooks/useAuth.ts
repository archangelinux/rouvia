import { useSession } from 'next-auth/react';
import { useState, useEffect, useCallback } from 'react';

interface VisitedPlace {
  place_name: string;
  place_id: string;
  activity_type: string;
  visited_date: string;
  location: string;
}

interface Preferences {
  favorite_cuisines: string[];
  budget_range: string;
  energy_level: number;
}

interface UserProfile {
  user_id: string;
  email: string;
  name: string;
  picture?: string;
  visited_places: VisitedPlace[];
  preferences: Preferences;
  created_at: string;
  last_updated: string;
}

interface UseAuthReturn {
  user: unknown;
  profile: UserProfile | null;
  isLoading: boolean;
  error: unknown;
  refetchProfile: () => Promise<void>;
  addVisitedPlace: (placeData: VisitedPlace) => Promise<boolean>;
  updatePreferences: (preferences: Partial<Preferences>) => Promise<boolean>;
}

export function useAuth(): UseAuthReturn {
  const { data: session, status } = useSession();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    if (!session?.user) return;
    
    setProfileLoading(true);
    try {
      // For now, we'll use a mock API call since we need to set up the backend
      // In production, this would be:
      // const response = await fetch('/api/user/profile', {
      //   headers: {
      //     'Authorization': `Bearer ${user.accessToken}`,
      //   },
      // });
      
      // Mock data for now
      const mockProfile: UserProfile = {
        user_id: session.user.id || 'mock_user_id',
        email: session.user.email || '',
        name: session.user.name || '',
        picture: session.user.image,
        visited_places: [
          {
            place_name: "Royal Ontario Museum",
            place_id: "rom_museum_toronto",
            activity_type: "entertainment",
            visited_date: "2024-01-15",
            location: "Toronto, ON"
          },
          {
            place_name: "Tim Hortons",
            place_id: "tim_hortons_waterloo",
            activity_type: "bites",
            visited_date: "2024-01-20",
            location: "Waterloo, ON"
          }
        ],
        preferences: {
          favorite_cuisines: ["italian", "asian"],
          budget_range: "moderate",
          energy_level: 5
        },
        created_at: "2024-01-01T00:00:00.000Z",
        last_updated: new Date().toISOString()
      };
      
      setProfile(mockProfile);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setProfileLoading(false);
    }
  }, [session?.user]);

  const addVisitedPlace = async (placeData: VisitedPlace): Promise<boolean> => {
    if (!session?.user || !profile) return false;
    
    try {
      // Mock API call for now
      // const response = await fetch('/api/user/profile/visited-places', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${user.accessToken}`,
      //   },
      //   body: JSON.stringify(placeData),
      // });
      
      // Mock success - add to local state
      const newPlace = {
        ...placeData,
        visited_date: new Date().toISOString(),
      };
      
      setProfile(prev => prev ? {
        ...prev,
        visited_places: [...prev.visited_places, newPlace],
        last_updated: new Date().toISOString()
      } : null);
      
      return true;
    } catch (error) {
      console.error('Failed to add visited place:', error);
      return false;
    }
  };

  const updatePreferences = async (preferences: Partial<Preferences>): Promise<boolean> => {
    if (!session?.user || !profile) return false;
    
    try {
      // Mock API call for now
      // const response = await fetch('/api/user/profile/preferences', {
      //   method: 'PUT',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${user.accessToken}`,
      //   },
      //   body: JSON.stringify(preferences),
      // });
      
      // Mock success - update local state
      setProfile(prev => prev ? {
        ...prev,
        preferences: { ...prev.preferences, ...preferences },
        last_updated: new Date().toISOString()
      } : null);
      
      return true;
    } catch (error) {
      console.error('Failed to update preferences:', error);
      return false;
    }
  };

  useEffect(() => {
    if (session?.user) {
      fetchProfile();
    } else {
      setProfile(null);
    }
  }, [session?.user, fetchProfile]);

  return {
    user: session?.user,
    profile,
    isLoading: status === 'loading' || profileLoading,
    error: null,
    refetchProfile: fetchProfile,
    addVisitedPlace,
    updatePreferences,
  };
}
