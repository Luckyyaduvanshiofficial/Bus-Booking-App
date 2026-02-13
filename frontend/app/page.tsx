'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { supabase } from '@/lib/supabase';

export default function Home() {
  const { user, isLoggedIn } = useAuthStore();
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check authentication status
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        useAuthStore.setState({
          user: session.user,
          isLoggedIn: true,
        });
      }
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl font-semibold">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100">
      {/* Header */}
      <header className="bg-white shadow">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold text-blue-600">🚍 Bus Booking</div>
          <div className="space-x-4">
            {isLoggedIn ? (
              <>
                <Link href="/dashboard" className="btn-primary text-sm">
                  Dashboard
                </Link>
                <button
                  onClick={() => {
                    supabase.auth.signOut();
                    useAuthStore.setState({ user: null, isLoggedIn: false });
                  }}
                  className="btn-secondary text-sm"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="btn-secondary text-sm">
                  Login
                </Link>
                <Link href="/register" className="btn-primary text-sm">
                  Register
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-16 flex flex-col items-center text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Book Your Bus Journey Today
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl">
          Search, compare, and book buses for weddings, tours, and group travel across Rajasthan
        </p>
        {isLoggedIn ? (
          <Link
            href="/search"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700"
          >
            Search Buses
          </Link>
        ) : (
          <Link
            href="/register"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700"
          >
            Get Started
          </Link>
        )}
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose Us</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: '⚡', title: 'Instant Booking', desc: 'Real-time availability and instant confirmation' },
              { icon: '💰', title: 'Best Prices', desc: 'Transparent pricing with no hidden charges' },
              { icon: '⭐', title: 'Verified Buses', desc: 'All buses are verified and certified' },
            ].map((feature) => (
              <div key={feature.title} className="card text-center">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p>&copy; 2026 Bus Booking Platform. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
