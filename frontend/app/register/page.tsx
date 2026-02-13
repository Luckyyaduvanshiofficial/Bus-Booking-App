'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    phone: '',
    email: '',
    firstName: '',
    lastName: '',
    role: 'customer',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Sign up with Supabase
      const { data, error: signupError } = await supabase.auth.signUp({
        phone: formData.phone.startsWith('+') ? formData.phone : `+${formData.phone}`,
        password: Math.random().toString(36).slice(-12), // Generate random password
        options: {
          data: {
            email: formData.email,
            first_name: formData.firstName,
            last_name: formData.lastName,
            role: formData.role,
          },
        },
      });

      if (signupError) throw signupError;
      setSuccess(true);

      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (err) {
      setError((err as any).message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-green-50">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="text-4xl mb-4">✅</div>
          <h2 className="text-2xl font-bold mb-2">Registration Successful!</h2>
          <p className="text-gray-600 mb-4">
            Please check your phone for the OTP. You'll be redirected to login shortly.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-50">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold text-center mb-6">🚍 Register</h1>

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="form-label">Phone Number</label>
            <input
              type="tel"
              name="phone"
              className="form-input"
              placeholder="919829012345"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>

          <div className="mb-4">
            <label className="form-label">Email</label>
            <input
              type="email"
              name="email"
              className="form-input"
              placeholder="you@example.com"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="form-label">First Name</label>
              <input
                type="text"
                name="firstName"
                className="form-input"
                placeholder="John"
                value={formData.firstName}
                onChange={handleChange}
                required
              />
            </div>
            <div>
              <label className="form-label">Last Name</label>
              <input
                type="text"
                name="lastName"
                className="form-input"
                placeholder="Doe"
                value={formData.lastName}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="mb-6">
            <label className="form-label">I am a:</label>
            <select
              name="role"
              className="form-input"
              value={formData.role}
              onChange={handleChange}
            >
              <option value="customer">Customer</option>
              <option value="operator">Bus Operator</option>
            </select>
          </div>

          <button
            type="submit"
            className="w-full btn-primary"
            disabled={loading}
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-4">
          Already have an account?{' '}
          <a href="/login" className="text-blue-600 font-semibold">
            Login
          </a>
        </p>
      </div>
    </div>
  );
}
