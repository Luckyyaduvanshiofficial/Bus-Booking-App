/**
 * Zustand auth store with Django backend integration.
 *
 * Auth Flow:
 * 1. sendOtp(phone) → triggers SMS via Supabase
 * 2. verifyOtp(phone, otp) → returns token + user
 * 3. (if new user) register(name, email) → completes profile
 *
 * Token is stored in memory (Zustand) — not localStorage per security rules.
 */

"use client";

import { create } from "zustand";
import type { User } from "@/types/api";
import {
  sendOtp as apiSendOtp,
  verifyOtp as apiVerifyOtp,
  registerUser as apiRegister,
  getProfile as apiGetProfile,
} from "@/lib/api";

interface AuthState {
  /* ── State ────────────────────────────────────────── */
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  /* ── Setters ──────────────────────────────────────── */
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;

  /* ── Auth Actions ─────────────────────────────────── */

  /** Send OTP to phone number. Returns success message. */
  sendOtp: (phone: string) => Promise<{ message: string }>;

  /** Verify OTP. Returns user + whether they need registration. */
  verifyOtp: (
    phone: string,
    otp: string
  ) => Promise<{ isNewUser: boolean }>;

  /** Complete registration for new users. */
  register: (
    data: { phone: string; name: string; email: string }
  ) => Promise<void>;

  /** Fetch and refresh user profile from backend. */
  refreshProfile: () => Promise<void>;

  /** Clear all auth state and sign out. */
  signOut: () => void;
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isLoading: false,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setToken: (token) => set({ token }),
  setLoading: (isLoading) => set({ isLoading }),

  sendOtp: async (phone: string) => {
    set({ isLoading: true });
    try {
      const response = await apiSendOtp(`+91${phone}`);
      return response;
    } finally {
      set({ isLoading: false });
    }
  },

  verifyOtp: async (phone: string, otp: string) => {
    set({ isLoading: true });
    try {
      const response = await apiVerifyOtp(`+91${phone}`, otp);
      set({
        user: response.user,
        token: response.token,
        isAuthenticated: true,
      });
      return { isNewUser: response.is_new_user };
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (data: { phone: string; name: string; email: string }) => {
    const { token } = get();
    if (!token) {
      throw new Error("Must verify OTP before registering");
    }
    set({ isLoading: true });
    try {
      const response = await apiRegister(token, {
        ...data,
        phone: `+91${data.phone}`,
      });
      set({
        user: response.user,
        token: response.token,
        isAuthenticated: true,
      });
    } finally {
      set({ isLoading: false });
    }
  },

  refreshProfile: async () => {
    try {
      const user = await apiGetProfile();
      set({ user, isAuthenticated: true });
    } catch {
      // If profile fetch fails, user is not authenticated
      set({ user: null, token: null, isAuthenticated: false });
    }
  },

  signOut: () =>
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    }),
}));
