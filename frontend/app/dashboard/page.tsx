'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { API } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const [userProfile, setUserProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn) {
      router.push('/login');
      return;
    }

    // Fetch user profile
    const fetchProfile = async () => {
      try {
        const response = await API.users.getProfile();
        setUserProfile(response.data);
      } catch (err) {
        console.error('Failed to fetch profile', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [isLoggedIn, router]);

  if (!isLoggedIn || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl font-semibold">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Welcome back, {userProfile?.first_name || 'User'}! 👋</h1>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Quick Links */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">🔍 Search Buses</h3>
            <a href="/search" className="btn-primary block text-center">
              Find Buses
            </a>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4">📅 My Bookings</h3>
            <a href="/my-bookings" className="btn-primary block text-center">
              View Bookings
            </a>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4">👤 My Profile</h3>
            <a href="/profile" className="btn-primary block text-center">
              Edit Profile
            </a>
          </div>

          {userProfile?.role === 'customer' && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">🚀 Become Operator</h3>
              <a href="/become-operator" className="btn-primary block text-center">
                Register Bus
              </a>
            </div>
          )}

          {userProfile?.role === 'operator' && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">🚍 My Buses</h3>
              <a href="/operator/buses" className="btn-primary block text-center">
                Manage Buses
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
