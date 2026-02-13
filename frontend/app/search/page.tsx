'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function SearchPage() {
  const [filters, setFilters] = useState({
    from: '',
    to: '',
    pickupDate: '',
    passengers: 1,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    // Handle search logic
    console.log('Searching for:', filters);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100">
      {/* Header */}
      <header className="bg-white shadow">
        <nav className="max-w-7xl mx-auto px-4 py-4">
          <Link href="/dashboard" className="text-xl font-bold text-blue-600">
            🚍 Bus Booking
          </Link>
        </nav>
      </header>

      {/* Search Card */}
      <div className="max-w-2xl mx-auto mt-8 px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold mb-6">Search Buses</h1>

          <form onSubmit={handleSearch}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="form-label">From</label>
                <input
                  type="text"
                  name="from"
                  className="form-input"
                  placeholder="Jaipur"
                  value={filters.from}
                  onChange={handleChange}
                  required
                />
              </div>

              <div>
                <label className="form-label">To</label>
                <input
                  type="text"
                  name="to"
                  className="form-input"
                  placeholder="Bharatpur"
                  value={filters.to}
                  onChange={handleChange}
                  required
                />
              </div>

              <div>
                <label className="form-label">Date</label>
                <input
                  type="date"
                  name="pickupDate"
                  className="form-input"
                  value={filters.pickupDate}
                  onChange={handleChange}
                  required
                />
              </div>

              <div>
                <label className="form-label">Passengers</label>
                <select
                  name="passengers"
                  className="form-input"
                  value={filters.passengers}
                  onChange={handleChange}
                >
                  {[...Array(50)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1} passenger{i > 0 ? 's' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700"
            >
              Search Buses
            </button>
          </form>
        </div>
      </div>

      {/* Results would appear here */}
      <div className="max-w-7xl mx-auto mt-8 px-4 pb-16">
        <div className="text-center text-gray-600">
          Enter your search criteria above to find available buses.
        </div>
      </div>
    </div>
  );
}
