/**
 * API client for the Bus Booking Platform.
 *
 * - Server components: use `serverFetch()` with native fetch + Next.js caching
 * - Client components: use `apiFetch()` with auth token injection
 *
 * All functions handle error mapping from backend error codes to user messages.
 */

import type { ApiError, PaginatedResponse } from "@/types/api";
import { ERROR_MESSAGES } from "@/lib/constants";

const API_BASE = "/api/v1";

/* ── Error handling ────────────────────────────────── */

export class ApiRequestError extends Error {
  code: string;
  statusCode: number;

  constructor(message: string, code: string, statusCode: number) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

/**
 * Map a backend error response to a user-friendly message.
 */
function mapErrorMessage(error: ApiError): string {
  return ERROR_MESSAGES[error.code] ?? error.error ?? "Something went wrong. Please try again.";
}

/* ── Client-side fetch wrapper ─────────────────────── */

/**
 * Fetch wrapper for client components with auth token injection.
 * Reads the Supabase session token and passes it as Django auth header.
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Get auth token from Supabase session (client-side)
  if (typeof window !== "undefined") {
    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        (headers as Record<string, string>)["Authorization"] =
          `Token ${session.access_token}`;
      }
    } catch {
      // Silently fail — unauthenticated request
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData: ApiError = { error: "Request failed", code: "UNKNOWN" };
    try {
      errorData = await response.json();
    } catch {
      // Response body not JSON
    }
    throw new ApiRequestError(
      mapErrorMessage(errorData),
      errorData.code,
      response.status
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/* ── Server-side fetch (for RSC) ───────────────────── */

/**
 * Fetch wrapper for server components. Uses native fetch with Next.js
 * revalidation caching. Does not inject auth tokens (public data only).
 */
export async function serverFetch<T>(
  endpoint: string,
  options: {
    revalidate?: number | false;
    tags?: string[];
  } = {}
): Promise<T> {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const url = `${backendUrl}/api/v1${endpoint}`;

  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    next: {
      revalidate: options.revalidate ?? 300,
      tags: options.tags,
    },
  });

  if (!response.ok) {
    let errorData: ApiError = { error: "Request failed", code: "UNKNOWN" };
    try {
      errorData = await response.json();
    } catch {
      // Not JSON
    }
    throw new ApiRequestError(
      mapErrorMessage(errorData),
      errorData.code,
      response.status
    );
  }

  return response.json();
}

/* ── Typed API functions ───────────────────────────── */

import type {
  Bus,
  BusSearchParams,
  Booking,
  PriceEstimate,
  AvailabilityDay,
  BusReview,
} from "@/types/api";

/** Search available buses (public, server-cacheable). */
export async function searchBuses(
  params: BusSearchParams
): Promise<PaginatedResponse<Bus>> {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach((v) => searchParams.append(key, String(v)));
      } else {
        searchParams.set(key, String(value));
      }
    }
  });

  return serverFetch<PaginatedResponse<Bus>>(
    `/buses/search/?${searchParams.toString()}`,
    { revalidate: 60, tags: ["buses"] }
  );
}

/** Get a single bus by ID (public). */
export async function getBus(id: string): Promise<Bus> {
  return serverFetch<Bus>(`/buses/${id}/`, {
    revalidate: 120,
    tags: [`bus-${id}`],
  });
}

/** Get bus reviews (public). */
export async function getBusReviews(
  busId: string,
  page = 1
): Promise<PaginatedResponse<BusReview>> {
  return serverFetch<PaginatedResponse<BusReview>>(
    `/reviews/bus/bus_reviews/?bus_id=${busId}&page=${page}`,
    { revalidate: 300, tags: [`reviews-${busId}`] }
  );
}

/** Get bus availability calendar (public). */
export async function getBusAvailability(
  busId: string,
  from?: string,
  to?: string
): Promise<AvailabilityDay[]> {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  return serverFetch<AvailabilityDay[]>(
    `/buses/${busId}/availability/?${params.toString()}`,
    { revalidate: 60 }
  );
}

/** Calculate price estimate (authenticated, client-side). */
export async function calculatePrice(data: {
  bus_id: string;
  pickup_location: string;
  drop_location: string;
  trip_type: string;
}): Promise<PriceEstimate> {
  return apiFetch<PriceEstimate>("/bookings/calculate-price/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Create a booking (authenticated, client-side). */
export async function createBooking(
  data: Record<string, unknown>
): Promise<Booking> {
  return apiFetch<Booking>("/bookings/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get current user's bookings (authenticated, client-side). */
export async function getMyBookings(
  page = 1
): Promise<PaginatedResponse<Booking>> {
  return apiFetch<PaginatedResponse<Booking>>(`/bookings/?page=${page}`);
}

/* ── Auth API functions ────────────────────────────── */

import type {
  SendOtpResponse,
  VerifyOtpResponse,
  RegisterResponse,
  User as UserType,
} from "@/types/api";

/**
 * Send OTP to an Indian phone number.
 * Phone must include country code (e.g. "+919876543210").
 */
export async function sendOtp(phone: string): Promise<SendOtpResponse> {
  const url = `${API_BASE}/auth/send-otp/`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone }),
  });

  if (!response.ok) {
    let errorData: ApiError = { error: "Failed to send OTP", code: "UNKNOWN" };
    try {
      errorData = await response.json();
    } catch {
      // Not JSON
    }
    throw new ApiRequestError(
      mapErrorMessage(errorData),
      errorData.code,
      response.status
    );
  }

  return response.json();
}

/**
 * Verify OTP and authenticate. Returns token + user.
 * For new users, `is_new_user` will be true — show registration form.
 */
export async function verifyOtp(
  phone: string,
  otp: string
): Promise<VerifyOtpResponse> {
  const url = `${API_BASE}/auth/verify-otp/`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp }),
  });

  if (!response.ok) {
    let errorData: ApiError = { error: "Verification failed", code: "UNKNOWN" };
    try {
      errorData = await response.json();
    } catch {
      // Not JSON
    }
    throw new ApiRequestError(
      mapErrorMessage(errorData),
      errorData.code,
      response.status
    );
  }

  return response.json();
}

/**
 * Complete registration for a new user (after OTP verification).
 * Requires the auth token from verifyOtp.
 */
export async function registerUser(
  token: string,
  data: { phone: string; name: string; email: string }
): Promise<RegisterResponse> {
  const url = `${API_BASE}/auth/register/`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify({ ...data, role: "customer" }),
  });

  if (!response.ok) {
    let errorData: ApiError = {
      error: "Registration failed",
      code: "UNKNOWN",
    };
    try {
      errorData = await response.json();
    } catch {
      // Not JSON
    }
    throw new ApiRequestError(
      mapErrorMessage(errorData),
      errorData.code,
      response.status
    );
  }

  return response.json();
}

/** Fetch the current user's profile (authenticated). */
export async function getProfile(): Promise<UserType> {
  return apiFetch<UserType>("/users/me/");
}
