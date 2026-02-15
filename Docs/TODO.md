# Bus Booking Platform — Development Roadmap & Todo List

**Project:** Bus Charter/Rental Marketplace (NOT RedBus Clone)  
**Business Model:** Customers rent ENTIRE buses for weddings, religious tours, family trips  
**Target Launch:** April 2026 (4-6 weeks remaining)  
**Status:** Backend ~95% Complete, Frontend ~15% Complete  
**Last Updated:** February 15, 2026

---

## 📊 Project Overview

```
Phase 1: Backend Foundation (Week 1-2)        [✅ COMPLETE]
Phase 1B: Critical Backend Features (Week 3)  [✅ COMPLETE]
Phase 1B-QA: Code Quality Review              [✅ COMPLETE]
Phase 2: Frontend Foundation (Week 3-4)       [🔄 45% DONE]
Phase 3: Core Features (Week 4-5)             [⏳ PENDING]
Phase 4: Integration & Testing (Week 5-6)     [⏳ PENDING]
Phase 5: Deployment & Launch (Week 6)         [⏳ PENDING]
```

## ⚠️ IMPORTANT: Charter/Rental Model (NOT Fixed-Route Transport)

**What This Platform IS:**

- Customers book ENTIRE bus (not per-seat like RedBus)
- Custom routes (pickup/drop defined by customer)
- Pricing = distance-based + per-day charges + amenities
- Operator accepts/rejects booking requests
- Use cases: Weddings (baraat), religious tours, corporate events

---

# ✅ BACKEND — COMPLETE (Phase 1 + 1B + QA)

All backend work is done. See previous version of this file for full Phase 1/1B task details.

**Backend API Summary:**
| App | Endpoints | Status |
|-----|-----------|--------|
| Users | Auth (OTP), Profile, Operators, Documents, Notifications | ✅ |
| Buses | CRUD, Photos, Amenities, Search, Availability, Date Blocking | ✅ |
| Bookings | CRUD, Accept/Reject, Cancel, Complete, Payments, Coupons, Price Calc | ✅ |
| Reviews | Bus Reviews, Operator Reviews, Admin Approval | ✅ |

---

# 🎨 PHASE 2: FRONTEND FOUNDATION [🔄 45% DONE]

**Duration:** Week 3-4  
**What's Done:** Design system, API client, layout components, homepage skeleton

## P2.1: Design System & Config ✅ DONE

- [x] `tailwind.config.ts` — Brand colors (Trust Blue, Travel Orange, Gold), Inter font
- [x] `globals.css` — HSL CSS variables, brand-aligned palette
- [x] `next.config.ts` — Cloudinary/Supabase images, API rewrite to Django
- [x] `layout.tsx` — Inter font, SEO metadata (OG/Twitter), React Query provider

## P2.2: Core Infrastructure ✅ DONE

- [x] `types/api.ts` — All backend model TypeScript interfaces (20+ types)
- [x] `lib/api.ts` — Dual-mode fetch (serverFetch for RSC, apiFetch for client + auth)
- [x] `lib/constants.ts` — Error messages, amenity icons, booking status badges, routes
- [x] `lib/providers.tsx` — React Query provider (5min stale, 10min cache)
- [x] `hooks/useAuth.ts` — Zustand auth store (user, token, signOut)

## P2.3: Layout Components ✅ DONE

- [x] `components/layout/Header.tsx` — Sticky nav, brand logo, mobile hamburger
- [x] `components/layout/Footer.tsx` — 4-column footer (Company, Operators, Routes, Brand)
- [x] `components/layout/MobileNav.tsx` — Fixed bottom nav (Home/Search/Bookings/Profile)
- [x] `components/layout/MainContainer.tsx` — max-w-7xl + padding enforcer
- [x] `components/layout/SectionWrapper.tsx` — py-16 spacing enforcer

## P2.4: Skeleton & Error Handling ✅ DONE

- [x] `components/skeletons/SkeletonCard.tsx` — Bus card loading skeleton
- [x] `components/skeletons/SkeletonSearchForm.tsx` — Search form skeleton
- [x] `components/skeletons/SkeletonRouteCard.tsx` — Route card skeleton
- [x] `app/loading.tsx` — Global loading fallback
- [x] `app/error.tsx` — Global error boundary with retry
- [x] `app/not-found.tsx` — Custom 404 page

## P2.5: SEO Foundation ✅ DONE

- [x] H1 on homepage, semantic HTML structure
- [x] JSON-LD Organization schema
- [x] Title template, OG/Twitter meta tags
- [x] `app/sitemap.ts` — Static route sitemap

## P2.6: Homepage ✅ DONE

- [x] `components/homepage/HeroSection.tsx` — Gradient bg + search card
- [x] `components/search/SearchForm.tsx` — From/To/Date/Passengers + swap
- [x] `components/homepage/FeaturesSection.tsx` — 4 trust icon cards
- [x] `components/homepage/HowItWorksSection.tsx` — 3-step flow
- [x] `components/homepage/RoutesSection.tsx` — 6 popular Rajasthan routes
- [x] `components/homepage/TestimonialsSection.tsx` — 3 review cards
- [x] `components/homepage/OperatorCTASection.tsx` — Operator conversion banner
- [x] Assembled `app/page.tsx` — All sections composed
- [x] Deleted starter template files (hero, deploy-button, logos, tutorial)

## P2.7: Authentication Pages ✅ DONE

> **Backend:** `POST /auth/send-otp/`, `POST /auth/verify-otp/`, `POST /auth/register/`

- [x] `lib/validations/auth.ts` — Zod schemas (phone 10-digit, OTP 6-digit, register name+email)
- [x] `types/api.ts` — Added `SendOtpResponse`, `VerifyOtpResponse`, `RegisterResponse`
- [x] `lib/api.ts` — Added `sendOtp()`, `verifyOtp()`, `registerUser()`, `getProfile()`
- [x] `hooks/useAuth.ts` — Rewritten with async auth methods (sendOtp, verifyOtp, register, signOut)
- [x] `hooks/useAuthGuard.ts` — Protected route hook (redirect + role-based access)
- [x] `components/auth/LoginPage.tsx` — 3-state phone→OTP→register flow
  - [x] Phone input with +91 prefix, 10-digit validation
  - [x] OTP 6-digit auto-focus inputs with paste support, 30s resend countdown
  - [x] Inline registration for new users (name + email)
  - [x] Error handling with user-friendly messages
- [x] `app/auth/login/page.tsx` — Brand-styled login page with SEO metadata
- [x] `components/layout/Header.tsx` — Dynamic auth state (user dropdown when logged in)
- [x] Deleted 12 starter template files (login-form, sign-up-form, forgot-password, etc.)
- [x] Build verified — `npx next build` exit code 0

## P2.8: Internationalization (i18n) ⏳ NOT STARTED

> **PRD:** Hindi + English bilingual support

- [ ] Create translation system (next-intl or custom context)
- [ ] English translation file (`en.json`)
- [ ] Hindi translation file (`hi.json`)
- [ ] Language toggle in Header
- [ ] Persist language preference
- [ ] Translate: homepage, search, booking, dashboard, auth pages

## P2.9: Toast Notification System ⏳ NOT STARTED

- [ ] Install shadcn toast (`npx shadcn@latest add toast`)
- [ ] Create `components/ui/Toaster.tsx` — Global toast container
- [ ] Wire API error handler to show toast on failure
- [ ] Success toasts for booking, payment, review actions

---

# 🔑 PHASE 3: CORE FEATURES [⏳ NOT STARTED]

**Duration:** Week 4-5  
**All pages below map directly to backend API endpoints**

## P3.1: Bus Search & Results Page

> **Backend:** `POST /buses/search/` (filters: base_city, capacity, ac, amenities, price, rating, availability, sort, pagination)

- [ ] `app/search/page.tsx` — Search results page
- [ ] `app/search/loading.tsx` — Search skeleton loader
- [ ] `components/search/SearchFilters.tsx` — Filter sidebar/bottom-sheet
  - [ ] Bus type filter (mini_bus, medium_bus, luxury_coach, tempo_traveller)
  - [ ] AC/Non-AC toggle
  - [ ] Price range slider (min/max)
  - [ ] Capacity range
  - [ ] Amenities checkboxes (music, pushback, charging, first_aid, etc.)
  - [ ] Rating filter (min stars)
  - [ ] Sort dropdown (price_asc, price_desc, rating_desc, capacity_desc, newest)
- [ ] `components/search/SearchResultCard.tsx` — Bus result card
  - [ ] Bus image (primary photo)
  - [ ] Name, operator, verified badge
  - [ ] Bus type + capacity label
  - [ ] Amenities icons row
  - [ ] Rating stars (gold) + review count
  - [ ] Price per km highlighted in orange
  - [ ] "View Details" CTA button
  - [ ] Hover lift animation (hover:-translate-y-1 hover:shadow-md)
- [ ] `components/search/ActiveFilters.tsx` — Active filter chips with remove
- [ ] `components/search/NoResults.tsx` — Empty state with suggestions
- [ ] Pagination component (not infinite scroll — per PRD)
- [ ] URL-based filter state (query params sync)
- [ ] Mobile: Bottom sheet filters (not sidebar)
- [ ] SEO: Dynamic meta title ("Buses from Jaipur to Udaipur | BusBook")

## P3.2: Bus Detail Page

> **Backend:** `GET /buses/{id}/`, `GET /buses/{id}/photos/`, `GET /buses/{id}/amenities/`, `GET /buses/{id}/availability/`, `GET /reviews/bus/bus_reviews/?bus_id={id}`

- [ ] `app/bus/[id]/page.tsx` — Bus detail page (server component)
- [ ] `app/bus/[id]/loading.tsx` — Detail page skeleton
- [ ] `components/bus/BusImageGallery.tsx` — Swipeable image gallery
  - [ ] Full-width hero image
  - [ ] Thumbnail strip below
  - [ ] Lightbox modal on click
  - [ ] Touch swipe on mobile
- [ ] `components/bus/BusSpecifications.tsx` — Type, capacity, AC, fuel, make/model, year
- [ ] `components/bus/BusAmenities.tsx` — Amenity icons with labels (from AMENITY_ICONS map)
- [ ] `components/bus/BusPricing.tsx` — Price breakdown card
  - [ ] Price per km (orange, bold)
  - [ ] Base price
  - [ ] Driver charge per day
  - [ ] Night halt charge
  - [ ] "Get exact quote" CTA → opens booking form
- [ ] `components/bus/OperatorCard.tsx` — Operator info
  - [ ] Business name + verified badge (blue bg)
  - [ ] Rating + total trips
  - [ ] Member since date
  - [ ] "Contact via WhatsApp" button
- [ ] `components/bus/AvailabilityCalendar.tsx` — 90-day calendar
  - [ ] Green = available, Red = blocked, Gray = past
  - [ ] Select date → enables booking
- [ ] `components/bus/BusReviews.tsx` — Paginated reviews
  - [ ] Star rating breakdown (5-star bar chart)
  - [ ] Individual review cards with rating, text, date
  - [ ] Pagination (load more)
- [ ] `components/bus/BookingCTA.tsx` — Sticky bottom CTA bar (mobile)
- [ ] SEO: Dynamic meta title ("{Bus Name} — Book on BusBook"), JSON-LD Product schema

## P3.3: Booking Flow (Multi-Step)

> **Backend:** `POST /bookings/calculate-price/`, `POST /bookings/`, `GET /bookings/{id}/`, coupon validation

- [ ] `app/booking/new/page.tsx` — Booking creation (protected route)
- [ ] `components/booking/BookingSteps.tsx` — Progress indicator (Step 1-2-3-4)
- [ ] **Step 1: Trip Details**
  - [ ] `components/booking/TripDetailsForm.tsx`
  - [ ] Pickup location (text + geocode)
  - [ ] Drop location (text + geocode)
  - [ ] Pickup date (calendar picker)
  - [ ] Return date (if round trip)
  - [ ] Pickup time
  - [ ] Trip type toggle (one_way / round_trip / multi_day)
  - [ ] Passenger count
  - [ ] Purpose selector (wedding, religious, family_trip, corporate, school_tour, other)
  - [ ] Special requests textarea
  - [ ] Zod validation
- [ ] **Step 2: Price Estimate**
  - [ ] `components/booking/PriceBreakdown.tsx`
  - [ ] Call `calculate-price` API with trip details
  - [ ] Show: base amount, driver charge, toll estimate, platform fee, total
  - [ ] Coupon code input + apply button
  - [ ] Discount display
  - [ ] Loading skeleton while calculating
- [ ] **Step 3: Payment Mode Selection**
  - [ ] `components/booking/PaymentModeSelector.tsx`
  - [ ] Online Full (100% now) — show full amount
  - [ ] Online Advance (₹3,000 now + rest to driver) — show split
  - [ ] Pay to Driver (₹500 booking fee + rest to driver) — show split
  - [ ] Trust badge: 🔒 "Secure Payment via Cashfree"
- [ ] **Step 4: Confirmation**
  - [ ] `components/booking/BookingConfirmation.tsx`
  - [ ] Summary of trip details + price + payment mode
  - [ ] "Confirm Booking" CTA → POST /bookings/
  - [ ] Loading state during submission
  - [ ] Success: redirect to booking detail page
  - [ ] Error: show user-friendly message from error code

## P3.4: Payment Integration

> **Backend:** `POST /bookings/{id}/initiate-payment/`, Cashfree webhook

- [ ] `components/payment/CashfreeCheckout.tsx` — Cashfree SDK integration
  - [ ] Initialize Cashfree drop-in UI
  - [ ] Handle payment success → redirect to booking detail
  - [ ] Handle payment failure → show retry option
  - [ ] Handle payment cancel → return to booking
- [ ] `app/booking/[id]/payment/page.tsx` — Payment page
  - [ ] Display amount, booking number, trust badges
  - [ ] Blue/white dominant (secure feel)
  - [ ] Orange CTA only
  - [ ] Show payment methods (UPI, Card, Net Banking)
- [ ] Payment status polling / webhook handling on frontend
- [ ] Payment receipt display

## P3.5: Customer Dashboard

> **Backend:** `GET /users/me/`, `GET /bookings/` (filtered by user)

- [ ] `app/dashboard/page.tsx` — Customer dashboard home
- [ ] `app/dashboard/layout.tsx` — Customer dashboard layout (sidebar + header)
- [ ] `components/dashboard/DashboardStats.tsx` — Booking count, upcoming trips, total spent
- [ ] `components/dashboard/UpcomingTrips.tsx` — Next 3 upcoming bookings
- [ ] `components/dashboard/QuickActions.tsx` — Search, Profile, Support links
- [ ] `components/dashboard/RecentActivity.tsx` — Recent booking/notification feed

## P3.6: Customer — My Bookings

> **Backend:** `GET /bookings/` (paginated, filtered by status), `GET /bookings/{id}/`, `POST /bookings/{id}/cancel/`

- [ ] `app/dashboard/bookings/page.tsx` — Booking list
- [ ] `components/dashboard/BookingTabs.tsx` — Tabs: All | Upcoming | Completed | Cancelled
- [ ] `components/dashboard/BookingListItem.tsx` — Booking row/card
  - [ ] Booking number, route, date, status badge
  - [ ] Bus name + operator
  - [ ] Amount + payment status
  - [ ] Action buttons (View, Cancel, Review)
- [ ] `app/dashboard/bookings/[id]/page.tsx` — Booking detail
  - [ ] Full trip details
  - [ ] Price breakdown
  - [ ] Payment history (from payment records)
  - [ ] Operator contact info
  - [ ] Cancel button (with confirmation modal + reason)
  - [ ] Download receipt (PDF generation)
- [ ] Status badge color mapping (pending=yellow, confirmed=green, cancelled=red, completed=blue)
- [ ] Loading skeletons for list + detail
- [ ] Empty state ("No bookings yet" with search CTA)
- [ ] Pagination (20 per page)

## P3.7: Customer — Profile & Settings

> **Backend:** `GET /users/me/`, `PUT /users/update_profile/`

- [ ] `app/dashboard/profile/page.tsx` — Profile page
  - [ ] Avatar upload (Cloudinary)
  - [ ] Edit name, email, city, address
  - [ ] Phone display (read-only — primary identifier)
  - [ ] Preferred language toggle (Hindi/English)
  - [ ] Account deletion request
- [ ] Form validation with Zod
- [ ] Success/error toast on save

## P3.8: Customer — Notifications

> **Backend:** `GET /notifications/`, `POST /notifications/{id}/mark-read/`

- [ ] `app/dashboard/notifications/page.tsx` — Notifications list
- [ ] `components/dashboard/NotificationItem.tsx` — Notification card
  - [ ] Icon by type (booking, payment, review)
  - [ ] Title + message
  - [ ] Timestamp (relative: "2 hours ago")
  - [ ] Read/unread indicator
  - [ ] Click → navigate to related booking
- [ ] Mark all as read button
- [ ] Notification bell in Header with unread count badge
- [ ] Pagination

## P3.9: Customer — Submit Review

> **Backend:** `POST /reviews/bus/`, `POST /reviews/operator/`

- [ ] `components/reviews/ReviewForm.tsx` — Review submission form
  - [ ] Star rating selectors (overall, cleanliness, punctuality, driver, value)
  - [ ] Review text textarea
  - [ ] Photo upload (optional, up to 3)
  - [ ] Submit button
  - [ ] Zod validation (min 1 star, optional text)
- [ ] Modal trigger from booking detail page
- [ ] Success toast + close modal

---

## P3.10: Operator Registration Flow

> **Backend:** `POST /auth/register/` (role=operator), `POST /documents/`, `GET /operators/registration-status/`

- [ ] `app/operator/register/page.tsx` — Multi-step operator registration
- [ ] `components/operator/registration/BusinessInfoForm.tsx` — Step 1
  - [ ] Business name, type, GST, PAN, address, city
- [ ] `components/operator/registration/BankDetailsForm.tsx` — Step 2
  - [ ] Account number, IFSC, beneficiary name
- [ ] `components/operator/registration/DocumentUploadForm.tsx` — Step 3
  - [ ] Aadhar, PAN, bank proof upload (Cloudinary)
  - [ ] File type + size validation
  - [ ] Upload progress indicator
- [ ] `components/operator/registration/RegistrationConfirmation.tsx` — Step 4
  - [ ] Summary of submitted info
  - [ ] "Pending verification" status
  - [ ] Timeline: submitted → under review → verified
- [ ] Progress bar (Step 1 → 2 → 3 → 4)
- [ ] Form persistence (don't lose data on refresh)
- [ ] Zod validation per step

## P3.11: Operator Dashboard

> **Backend:** `GET /operators/dashboard/`, `GET /operators/earnings/`

- [ ] `app/operator/dashboard/page.tsx` — Operator dashboard home
- [ ] `app/operator/dashboard/layout.tsx` — Operator layout (different sidebar from customer)
- [ ] `components/operator/DashboardStats.tsx` — Revenue, bookings, rating, pending requests
- [ ] `components/operator/EarningsChart.tsx` — Monthly earnings graph
- [ ] `components/operator/PendingBookings.tsx` — Bookings needing accept/reject
- [ ] `components/operator/UpcomingTrips.tsx` — Confirmed upcoming trips

## P3.12: Operator — My Buses

> **Backend:** `GET /buses/my_buses/`, `POST /buses/`, `PUT /buses/{id}/`, `DELETE /buses/{id}/`, `POST /buses/{id}/photos/`, `POST /buses/{id}/amenities/`, `GET /buses/{id}/availability/`, `POST /buses/{id}/block-dates/`, `DELETE /buses/{id}/unblock-date/{date}/`

- [ ] `app/operator/buses/page.tsx` — Bus list
- [ ] `components/operator/BusList.tsx` — List of operator's buses
  - [ ] Bus card: photo, name, registration, status, rating, trip count
  - [ ] Status: Active / Pending Approval / Rejected
  - [ ] Actions: Edit, Calendar, Deactivate
- [ ] `app/operator/buses/new/page.tsx` — Add new bus form
  - [ ] `components/operator/BusForm.tsx` — Bus creation/edit form
  - [ ] Fields: name, type, capacity, registration, make/model, year, AC type, fuel
  - [ ] Pricing: base_price, price_per_km, driver_charge, night_charge
  - [ ] Photo upload (up to 10, drag-and-drop, reorder)
  - [ ] Amenities selector (checkbox grid with icons)
  - [ ] Base city, base area
  - [ ] Zod validation
- [ ] `app/operator/buses/[id]/edit/page.tsx` — Edit bus
- [ ] `app/operator/buses/[id]/calendar/page.tsx` — Availability calendar
  - [ ] 90-day calendar view
  - [ ] Click date to block/unblock
  - [ ] Show booked dates (from platform)
  - [ ] Show manually blocked dates
  - [ ] Add block reason + notes

## P3.13: Operator — Booking Management

> **Backend:** `GET /bookings/` (operator filter), `POST /bookings/{id}/accept/`, `POST /bookings/{id}/reject/`, `POST /bookings/{id}/complete/`, `POST /bookings/{id}/mark-paid-to-driver/`

- [ ] `app/operator/bookings/page.tsx` — Operator booking list
- [ ] `components/operator/BookingTabs.tsx` — Tabs: Pending | Upcoming | Completed | All
- [ ] `components/operator/PendingBookingCard.tsx` — Accept/reject card
  - [ ] Customer name + phone
  - [ ] Trip details (route, date, passengers, purpose)
  - [ ] Estimated revenue
  - [ ] Accept button (green)
  - [ ] Reject button (red) + reason input modal
  - [ ] Countdown timer (2h expiry)
- [ ] `app/operator/bookings/[id]/page.tsx` — Booking detail
  - [ ] Complete trip details
  - [ ] Customer contact info
  - [ ] Payment status + amounts
  - [ ] "Mark as Completed" button
  - [ ] "Cash Received from Customer" button (for advance payment mode)
- [ ] Loading skeletons
- [ ] Empty state per tab

## P3.14: Operator — Documents

> **Backend:** `GET /documents/`, `POST /documents/`, `GET /documents/{id}/`

- [ ] `app/operator/documents/page.tsx` — Document management
- [ ] `components/operator/DocumentList.tsx` — Document list with status
  - [ ] Document type, upload date, status badge
  - [ ] Verified ✅ / Pending ⏰ / Rejected ❌
  - [ ] Re-upload button for rejected docs
  - [ ] Expiry date warning
- [ ] `components/operator/DocumentUpload.tsx` — Upload form
  - [ ] Document type selector
  - [ ] File upload (PDF/image, max 5MB)
  - [ ] Document number input
  - [ ] Expiry date input
  - [ ] Upload progress bar

## P3.15: Operator — Earnings & Payouts

> **Backend:** `GET /operators/earnings/`, `GET /bookings/payments/`

- [ ] `app/operator/earnings/page.tsx` — Earnings page
- [ ] `components/operator/EarningsSummary.tsx` — Total, this month, pending payout
- [ ] `components/operator/EarningsTable.tsx` — Transaction history
  - [ ] Booking number, date, amount, commission, payout, status
  - [ ] Pagination
- [ ] `components/operator/PayoutInfo.tsx` — Bank details + next payout date

---

## P3.16: Admin Dashboard (Basic — Django Admin Primary)

> **Backend:** Django Admin at /admin/ handles most admin work. Frontend admin is supplementary.

- [ ] `app/admin/dashboard/page.tsx` — Admin overview
- [ ] `components/admin/PlatformStats.tsx` — Total users, bookings, revenue, operators
- [ ] `components/admin/PendingVerifications.tsx` — Operators awaiting verification
  - [ ] Approve / Reject buttons
  - [ ] View submitted documents
- [ ] `components/admin/RecentBookings.tsx` — Latest bookings across platform
- [ ] `components/admin/FlaggedReviews.tsx` — Reviews needing approval
  - [ ] Approve / Delete buttons
- [ ] Admin layout with admin-specific navigation

---

# 🔗 PHASE 4: INTEGRATION & POLISH [⏳ NOT STARTED]

**Duration:** Week 5-6

## P4.1: Cashfree Payment Gateway

- [ ] Setup Cashfree sandbox account
- [ ] Integrate Cashfree Drop-in SDK
- [ ] Test UPI, Card, Net Banking flows
- [ ] Handle webhook for payment confirmation
- [ ] Handle refund display on booking cancellation
- [ ] Production config switch

## P4.2: Cloudinary Integration

- [ ] Create Cloudinary upload wrapper component
- [ ] Bus photo upload (operator)
- [ ] Document upload (operator)
- [ ] Avatar upload (all users)
- [ ] Review photo upload (customer)
- [ ] Image optimization (auto-format, compression)
- [ ] Upload progress bars

## P4.3: Location Services

- [ ] Location autocomplete for search (OpenStreetMap Nominatim — free)
- [ ] Location autocomplete for booking form
- [ ] Route visualization on bus detail (optional)

## P4.4: PWA Configuration

> **PRD:** Mobile-first PWA

- [ ] `public/manifest.json` — App name, icons, theme color
- [ ] Service worker setup (next-pwa or custom)
- [ ] Offline fallback page
- [ ] Add to homescreen prompt
- [ ] App icons (192x192, 512x512)

## P4.5: Performance Optimization

- [ ] Lighthouse audit ≥ 90 on all pages
- [ ] Bundle analysis (next-bundle-analyzer)
- [ ] Dynamic imports for Framer Motion, Cashfree SDK
- [ ] Image optimization audit (all images via next/image)
- [ ] Core Web Vitals: LCP < 2.5s, CLS < 0.1, FID < 100ms

## P4.6: Email Templates

- [ ] Booking confirmation email template
- [ ] Payment receipt template
- [ ] Review reminder template
- [ ] Operator verification status template

## P4.7: WhatsApp Integration

- [ ] WhatsApp click-to-chat link (operator profile, booking detail)
- [ ] Pre-filled message with booking reference

---

# ✅ PHASE 5: TESTING & SECURITY [⏳ NOT STARTED]

**Duration:** Week 6

## P5.1: Frontend Testing

- [ ] Component unit tests (Jest + React Testing Library)
- [ ] Form validation tests
- [ ] API error handling tests
- [ ] Loading/error state tests
- [ ] Accessibility audit (axe-core, keyboard nav, screen readers)

## P5.2: Integration Testing

- [ ] Complete booking flow E2E (search → detail → book → pay → confirm)
- [ ] Operator flow E2E (register → add bus → accept booking)
- [ ] Auth flow E2E (OTP → login → logout)
- [ ] Payment flow E2E (initiate → Cashfree sandbox → webhook → confirm)

## P5.3: Cross-Device Testing

- [ ] Mobile (375px, 414px) — iOS Safari, Android Chrome
- [ ] Tablet (768px, 1024px)
- [ ] Desktop (1280px, 1440px, 1920px)
- [ ] Touch interactions on mobile
- [ ] Bottom sheet filters on mobile

## P5.4: Security Audit

- [ ] No secrets in frontend code
- [ ] httpOnly cookies for auth tokens
- [ ] Input sanitization
- [ ] CSRF protection verified
- [ ] Rate limiting on sensitive endpoints
- [ ] Error messages don't expose internals

## P5.5: Performance Testing

- [ ] Lighthouse ≥ 90 all pages
- [ ] JS bundle < 250kb initial
- [ ] No N+1 query issues in server components
- [ ] Image lazy loading verified
- [ ] Skeleton loading for all async content

---

# 🚀 PHASE 6: DEPLOYMENT & LAUNCH [⏳ NOT STARTED]

**Duration:** Week 6-7

## P6.1: Backend Deployment (Heroku)

- [ ] Create Heroku app, configure env vars
- [ ] PostgreSQL on Heroku
- [ ] Production Django settings (DEBUG=False, ALLOWED_HOSTS)
- [ ] SSL/HTTPS
- [ ] Run migrations, create superuser
- [ ] Sentry error tracking
- [ ] Celery worker dyno

## P6.2: Frontend Deployment (Vercel)

- [ ] Connect GitHub repo to Vercel
- [ ] Configure env vars (NEXT*PUBLIC_SUPABASE*\*, BACKEND_URL)
- [ ] Custom domain setup
- [ ] Preview deployments for PRs
- [ ] Google Analytics

## P6.3: Production Third-Party Setup

- [ ] Cashfree production merchant account
- [ ] Cloudinary production account
- [ ] MSG91 production configuration
- [ ] n8n webhook configuration
- [ ] Sentry for frontend + backend

## P6.4: Launch Checklist

- [ ] All pages functional
- [ ] Payments tested with real cards
- [ ] OTP flow works on real phones
- [ ] Error pages styled (404, 500, error boundary)
- [ ] SEO verified (meta, sitemap, JSON-LD)
- [ ] Favicon + OG image set
- [ ] Performance audit passed
- [ ] Security audit passed

## P6.5: Soft Launch

- [ ] Deploy with limited access
- [ ] Test with 5-10 real users
- [ ] Gather feedback
- [ ] Fix critical bugs
- [ ] Monitor Sentry for errors

## P6.6: Official Launch

- [ ] Full production deploy
- [ ] Monitor for 48 hours
- [ ] User support plan ready

---

# 📊 Progress Tracker

| Phase                         | Status         | Completion |
| ----------------------------- | -------------- | ---------- |
| Phase 1: Backend Foundation   | ✅ Complete    | 100%       |
| Phase 1B: Critical Features   | ✅ Complete    | 100%       |
| Phase 1B-QA: Code Quality     | ✅ Complete    | 100%       |
| Phase 2: Frontend Foundation  | 🔄 In Progress | ~40%       |
| Phase 3: Core Features        | ⏳ Pending     | 0%         |
| Phase 4: Integration & Polish | ⏳ Pending     | 0%         |
| Phase 5: Testing & Security   | ⏳ Pending     | 0%         |
| Phase 6: Deployment & Launch  | ⏳ Pending     | 0%         |
| **Overall Project**           | **🔄**         | **~55%**   |

## Frontend Page Count

| Category                                | Pages         | Status     |
| --------------------------------------- | ------------- | ---------- |
| Homepage                                | 1             | ✅ Done    |
| Auth (Login, Register)                  | 2             | ⏳         |
| Search Results                          | 1             | ⏳         |
| Bus Detail                              | 1             | ⏳         |
| Booking Flow                            | 2             | ⏳         |
| Customer Dashboard                      | 5             | ⏳         |
| Operator Registration                   | 1             | ⏳         |
| Operator Dashboard                      | 6             | ⏳         |
| Admin Dashboard                         | 1             | ⏳         |
| Static (About, Contact, Terms, Privacy) | 4             | ⏳         |
| Error Pages (404, Error)                | 2             | ✅ Done    |
| **Total**                               | **~26 pages** | **3 done** |

---

**Created:** February 12, 2026  
**Last Updated:** February 15, 2026  
**Status:** Backend ~95% Complete | Frontend ~10% | ~55% Overall  
**Developer:** You! 🚀
