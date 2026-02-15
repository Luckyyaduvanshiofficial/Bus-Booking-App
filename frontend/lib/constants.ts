/**
 * Application-wide constants: error messages, amenity icons,
 * booking status maps, navigation links, and popular routes data.
 */

import {
  Music,
  Armchair,
  Plug,
  Cross,
  Flame,
  Lamp,
  Luggage,
  Droplets,
  Disc3,
  Wifi,
  Monitor,
  type LucideIcon,
} from "lucide-react";

/* ── Error code → user message mapping ─────────────── */

export const ERROR_MESSAGES: Record<string, string> = {
  // Auth
  "USR-SERV-AUTH-001": "Unable to send OTP. Please try again.",
  "USR-SERV-AUTH-002": "Invalid OTP. Please check and try again.",
  "USR-SERV-AUTH-003": "Invalid credentials. Please check your phone number.",
  "USR-VIEWS-AUTH-001": "Please log in to continue.",

  // Booking
  "BOK-SERV-CONFLICT-001": "This bus is not available on your selected date.",
  "BOK-SERV-CONFLICT-003": "Only confirmed bookings can be completed.",
  "BOK-SERV-VAL-001": "This booking is no longer in pending status.",
  "BOK-SERV-VAL-002": "Invalid response. Please accept or reject.",
  "BOK-VIEWS-PERM-002": "Only the operator can accept or reject bookings.",
  "BOK-VIEWS-PERM-003": "You are not authorized to cancel this booking.",
  "BOK-VIEWS-VAL-001": "This booking cannot be cancelled in its current status.",

  // Payment
  "PAY-SERV-VAL-001": "Payment verification failed. Please contact support.",
  "PAY-VIEWS-NOTFOUND-001": "Payment record not found.",
  "PAY-VIEWS-PERM-001": "Only admins can confirm payments manually.",

  // Review
  "REV-VIEWS-VAL-001": "Bus ID is required to view reviews.",
  "REV-VIEWS-VAL-002": "Operator ID is required to view reviews.",
  "REV-VIEWS-VAL-003": "You can only review operators you have completed a booking with.",

  // Generic
  UNKNOWN: "Something went wrong. Please try again.",
};

/* ── Amenity key → icon component mapping ──────────── */

export const AMENITY_ICONS: Record<string, { icon: LucideIcon; label: string }> = {
  music_system: { icon: Music, label: "Music System" },
  pushback_seats: { icon: Armchair, label: "Pushback Seats" },
  charging_points: { icon: Plug, label: "Charging Points" },
  first_aid: { icon: Cross, label: "First Aid" },
  fire_extinguisher: { icon: Flame, label: "Fire Extinguisher" },
  reading_lights: { icon: Lamp, label: "Reading Lights" },
  luggage_space: { icon: Luggage, label: "Luggage Space" },
  water_bottles: { icon: Droplets, label: "Water Bottles" },
  dj_system: { icon: Disc3, label: "DJ System" },
  wifi: { icon: Wifi, label: "WiFi" },
  tv_screen: { icon: Monitor, label: "TV Screen" },
};

/* ── Booking status → badge config ─────────────────── */

export const BOOKING_STATUS_MAP: Record<
  string,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { label: "Pending", variant: "secondary" },
  confirmed: { label: "Confirmed", variant: "default" },
  in_progress: { label: "In Progress", variant: "default" },
  completed: { label: "Completed", variant: "outline" },
  cancelled_by_customer: { label: "Cancelled", variant: "destructive" },
  cancelled_by_operator: { label: "Cancelled by Operator", variant: "destructive" },
  expired: { label: "Expired", variant: "secondary" },
};

/* ── Navigation links ──────────────────────────────── */

export const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/search", label: "Search Buses" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
] as const;

export const OPERATOR_NAV_LINKS = [
  { href: "/operator/dashboard", label: "Dashboard" },
  { href: "/operator/buses", label: "My Buses" },
  { href: "/operator/bookings", label: "Bookings" },
  { href: "/operator/earnings", label: "Earnings" },
  { href: "/operator/documents", label: "Documents" },
] as const;

/* ── Popular routes (homepage data) ────────────────── */

export interface PopularRoute {
  from: string;
  to: string;
  distance: string;
  estimatedPrice: string;
  imageKey: string;
}

export const POPULAR_ROUTES: PopularRoute[] = [
  {
    from: "Jaipur",
    to: "Udaipur",
    distance: "393 km",
    estimatedPrice: "₹12,000",
    imageKey: "udaipur",
  },
  {
    from: "Jaipur",
    to: "Jodhpur",
    distance: "335 km",
    estimatedPrice: "₹10,500",
    imageKey: "jodhpur",
  },
  {
    from: "Jaipur",
    to: "Jaisalmer",
    distance: "558 km",
    estimatedPrice: "₹16,000",
    imageKey: "jaisalmer",
  },
  {
    from: "Jaipur",
    to: "Pushkar",
    distance: "150 km",
    estimatedPrice: "₹5,500",
    imageKey: "pushkar",
  },
  {
    from: "Jaipur",
    to: "Mount Abu",
    distance: "490 km",
    estimatedPrice: "₹14,500",
    imageKey: "mountabu",
  },
  {
    from: "Jaipur",
    to: "Bharatpur",
    distance: "180 km",
    estimatedPrice: "₹6,000",
    imageKey: "bharatpur",
  },
];

/* ── Bus type labels ───────────────────────────────── */

export const BUS_TYPE_LABELS: Record<string, string> = {
  mini_bus: "Mini Bus",
  medium_bus: "Medium Bus",
  luxury_coach: "Luxury Coach",
  tempo_traveller: "Tempo Traveller",
};

/* ── Trip type labels ──────────────────────────────── */

export const TRIP_TYPE_LABELS: Record<string, string> = {
  one_way: "One Way",
  round_trip: "Round Trip",
  multi_day: "Multi-Day",
};
