/**
 * TypeScript interfaces for all backend API models.
 * Maps 1:1 to Django REST Framework serializer output.
 *
 * Note: Django Decimal fields are serialized as strings — parse with parseFloat().
 * Note: Django dates are ISO-8601 strings — parse with new Date().
 */

/* ── Pagination ────────────────────────────────────── */

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/* ── API Error ─────────────────────────────────────── */

export interface ApiError {
  error: string;
  code: string;
}

/* ── User & Auth ───────────────────────────────────── */

export type UserRole = "customer" | "operator" | "admin";
export type VerificationStatus = "pending" | "verified" | "rejected";
export type SubscriptionTier = "free" | "pro" | "enterprise";

export interface User {
  id: string;
  phone: string;
  name: string | null;
  email: string | null;
  role: UserRole;
  avatar_url: string | null;
  business_name: string | null;
  business_type: string | null;
  gst_number: string | null;
  pan_number: string | null;
  address: string | null;
  city: string | null;
  is_verified: boolean;
  verification_status: VerificationStatus;
  rating_avg: string;
  rating_count: number;
  total_bookings: number;
  subscription_tier: SubscriptionTier;
  preferred_language: "hi" | "en";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OTPRequest {
  phone: string;
}

export interface OTPVerify {
  phone: string;
  otp: string;
}

export interface AuthTokenResponse {
  token: string;
  user: User;
}

/** Response from POST /auth/send-otp/ */
export interface SendOtpResponse {
  message: string;
}

/** Response from POST /auth/verify-otp/ */
export interface VerifyOtpResponse extends AuthTokenResponse {
  is_new_user: boolean;
}

/** Response from POST /auth/register/ */
export interface RegisterResponse extends AuthTokenResponse {
  created: boolean;
}

/* ── Bus ───────────────────────────────────────────── */

export type BusType =
  | "mini_bus"
  | "medium_bus"
  | "luxury_coach"
  | "tempo_traveller";
export type ACType = "ac" | "non_ac" | "both";
export type FuelType = "diesel" | "cng" | "electric";
export type ApprovalStatus = "pending" | "approved" | "rejected";

export type AmenityKey =
  | "music_system"
  | "pushback_seats"
  | "charging_points"
  | "first_aid"
  | "fire_extinguisher"
  | "reading_lights"
  | "luggage_space"
  | "water_bottles"
  | "dj_system"
  | "wifi"
  | "tv_screen";

export interface BusPhoto {
  id: string;
  bus_id: string;
  photo_url: string;
  photo_type: string;
  display_order: number;
  is_primary: boolean;
  created_at: string;
}

export interface BusAmenity {
  id: string;
  bus_id: string;
  amenity: AmenityKey;
}

export interface Bus {
  id: string;
  operator_id: string;
  operator?: User;
  name: string;
  description: string | null;
  bus_type: BusType;
  seating_capacity: number;
  registration_number: string;
  make_model: string | null;
  manufacture_year: number | null;
  ac_type: ACType;
  fuel_type: FuelType;
  price_per_km: string;
  base_price: string | null;
  driver_charge: string;
  night_charge: string;
  base_city: string;
  base_area: string | null;
  is_active: boolean;
  is_approved: boolean;
  approval_status: ApprovalStatus;
  rating_avg: string;
  rating_count: number;
  total_trips: number;
  photos: BusPhoto[];
  amenities: BusAmenity[];
  created_at: string;
  updated_at: string;
}

/* ── Booking ───────────────────────────────────────── */

export type TripType = "one_way" | "round_trip" | "multi_day";
export type BookingStatus =
  | "pending"
  | "confirmed"
  | "in_progress"
  | "completed"
  | "cancelled_by_customer"
  | "cancelled_by_operator"
  | "expired";
export type PaymentMode = "online_full" | "online_advance" | "pay_driver";
export type PaymentStatus =
  | "pending"
  | "advance_paid"
  | "fully_paid"
  | "refunded";
export type BookingPurpose =
  | "wedding"
  | "religious"
  | "family_trip"
  | "corporate"
  | "school_tour"
  | "other";

export interface Booking {
  id: string;
  booking_number: string;
  customer_id: string;
  customer?: User;
  operator_id: string;
  operator?: User;
  bus_id: string;
  bus?: Bus;
  trip_type: TripType;
  pickup_location: string;
  pickup_lat: string | null;
  pickup_lng: string | null;
  drop_location: string;
  drop_lat: string | null;
  drop_lng: string | null;
  pickup_date: string;
  pickup_time: string;
  return_date: string | null;
  passenger_count: number;
  purpose: BookingPurpose | null;
  special_requests: string | null;
  estimated_km: string | null;
  estimated_route: string | null;
  base_amount: string;
  driver_charge: string;
  night_charge: string;
  toll_estimate: string;
  platform_fee: string;
  discount_amount: string;
  total_amount: string;
  commission_rate: string;
  commission_amount: string;
  operator_payout: string;
  status: BookingStatus;
  operator_response: string | null;
  operator_response_at: string | null;
  rejection_reason: string | null;
  payment_mode: PaymentMode;
  payment_status: PaymentStatus;
  advance_amount: string;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  refund_amount: string;
  completed_at: string | null;
  operator_payout_status: string;
  operator_payout_at: string | null;
  created_at: string;
  updated_at: string;
}

/* ── Payment ───────────────────────────────────────── */

export type PaymentType = "advance" | "full" | "remaining" | "refund";
export type PaymentMethod = "upi" | "card" | "netbanking" | "wallet";
export type TransactionStatus =
  | "created"
  | "authorized"
  | "captured"
  | "failed"
  | "refunded";

export interface Payment {
  id: string;
  booking_id: string;
  cf_order_id: string | null;
  cf_payment_id: string | null;
  amount: string;
  currency: string;
  payment_type: PaymentType;
  payment_method: PaymentMethod | null;
  status: TransactionStatus;
  created_at: string;
  updated_at: string;
}

/* ── Review ────────────────────────────────────────── */

export interface BusReview {
  id: string;
  booking_id: string;
  customer_id: string;
  customer?: User;
  bus_id: string;
  operator_id: string;
  rating_overall: number;
  rating_cleanliness: number | null;
  rating_punctuality: number | null;
  rating_driver: number | null;
  rating_value: number | null;
  review_text: string | null;
  photo_urls: string[];
  is_approved: boolean;
  is_flagged: boolean;
  created_at: string;
}

/* ── Coupon ────────────────────────────────────────── */

export interface Coupon {
  id: string;
  code: string;
  description: string | null;
  discount_type: "flat" | "percentage";
  discount_value: string;
  max_discount: string | null;
  min_booking: string;
  usage_limit: number | null;
  used_count: number;
  per_user_limit: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
  created_at: string;
}

/* ── Notification ──────────────────────────────────── */

export type NotificationType =
  | "booking_confirmed"
  | "booking_cancelled"
  | "new_review"
  | "payment_received"
  | "document_verified";

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

/* ── Search & Utility ──────────────────────────────── */

export interface BusSearchParams {
  from?: string;
  to?: string;
  date?: string;
  passengers?: number;
  bus_type?: BusType;
  ac_type?: ACType;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  amenities?: AmenityKey[];
  sort?: "price_asc" | "price_desc" | "rating_desc" | "capacity_desc" | "newest";
  page?: number;
}

export interface PriceEstimate {
  base_amount: string;
  driver_charge: string;
  toll_estimate: string;
  platform_fee: string;
  total_amount: string;
  estimated_km: string;
}

export interface AvailabilityDay {
  date: string;
  is_available: boolean;
  reason: string | null;
  notes: string | null;
}

/* ── Operator Dashboard ────────────────────────────── */

export interface OperatorDashboard {
  total_bookings: number;
  month_revenue: string;
  average_rating: string;
  pending_requests: number;
  upcoming_trips: number;
}

/* ── Document ──────────────────────────────────────── */

export type DocumentType =
  | "aadhar"
  | "pan"
  | "bank_proof"
  | "rc"
  | "fitness_certificate"
  | "permit"
  | "insurance"
  | "puc"
  | "road_tax"
  | "driver_license"
  | "driver_aadhar"
  | "police_verification"
  | "gst_certificate"
  | "trade_license"
  | "company_registration";

export interface OperatorDocument {
  id: string;
  user_id: string;
  bus_id: string | null;
  document_type: DocumentType;
  document_url: string;
  document_number: string | null;
  expiry_date: string | null;
  verification_status: VerificationStatus;
  verified_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}
