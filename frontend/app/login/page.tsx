'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/lib/store';

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        phone: phone.startsWith('+') ? phone : `+${phone}`,
      });

      if (error) throw error;
      setOtpSent(true);
    } catch (err) {
      setError((err as any).message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data, error } = await supabase.auth.verifyOtp({
        phone: phone.startsWith('+') ? phone : `+${phone}`,
        token: otp,
        type: 'sms',
      });

      if (error) throw error;

      if (data.user) {
        useAuthStore.setState({
          user: data.user,
          isLoggedIn: true,
        });
        router.push('/dashboard');
      }
    } catch (err) {
      setError((err as any).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-50">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold text-center mb-6">🚍 Login</h1>

        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}

        {!otpSent ? (
          <form onSubmit={handleSendOTP}>
            <div className="mb-4">
              <label className="form-label">Phone Number</label>
              <input
                type="tel"
                className="form-input"
                placeholder="919829012345"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="w-full btn-primary"
              disabled={loading}
            >
              {loading ? 'Sending OTP...' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP}>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-4">
                OTP sent to {phone}. Enter it below to login.
              </p>
              <label className="form-label">OTP</label>
              <input
                type="text"
                className="form-input"
                placeholder="000000"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="w-full btn-primary"
              disabled={loading}
            >
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>

            <button
              type="button"
              onClick={() => {
                setOtpSent(false);
                setOtp('');
              }}
              className="w-full btn-secondary mt-2"
            >
              Back
            </button>
          </form>
        )}

        <p className="text-center text-gray-600 mt-4">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-600 font-semibold">
            Register
          </a>
        </p>
      </div>
    </div>
  );
}
