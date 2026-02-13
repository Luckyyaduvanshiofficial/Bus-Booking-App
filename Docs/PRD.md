# 🚍 BUS BOOKING PLATFORM — PRODUCT REQUIREMENTS DOCUMENT (PRD)

**Version:** 2.0  
**Date:** February 12, 2026  
**Author:** Founder (MCA Student, Jaipur)  
**Status:** Finalized — Ready to Build  
**Target Launch:** April 2026 (6-8 weeks)  
**Developer:** Solo (Founder)  
**Backend:** Django + DRF  
**Hosting:** Heroku ($320 credits) + Vercel (free)  
**Payments:** Cashfree

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Final Tech Stack](#2-final-tech-stack)
3. [System Architecture](#3-system-architecture)
4. [Database Schema](#4-database-schema)
5. [API Endpoints](#5-api-endpoints)
6. [Feature Specifications](#6-feature-specifications)
7. [User Roles & Permissions](#7-user-roles--permissions)
8. [UI/UX Screens](#8-uiux-screens)
9. [n8n Automation Workflows](#9-n8n-automation-workflows)
10. [Payment Flow](#10-payment-flow)
11. [Internationalization (Hindi + English)](#11-internationalization-hindi--english)
12. [PWA Configuration](#12-pwa-configuration)
13. [Deployment Plan](#13-deployment-plan)
14. [Development Sprint Plan](#14-development-sprint-plan)
15. [Testing Strategy](#15-testing-strategy)
16. [Cost Breakdown](#16-cost-breakdown)
17. [Open Decisions](#17-open-decisions)

---

## 1. EXECUTIVE SUMMARY

### What We're Building
A **two-sided marketplace** (mobile-first PWA + web) connecting **bus/mini-bus operators** with **customers** who need private charter bookings in Rajasthan, starting with Jaipur.

### Core User Flows
1. **Customer** → Search buses → View details → Book → Pay → Rate
2. **Operator** → Register → List buses → Receive bookings → Complete trip → Get paid
3. **Admin** → Approve operators → Manage disputes → Monitor platform

### MVP Scope (6-Week Build)
| Included in MVP | Excluded from MVP (v2) |
|---|---|
| Customer search + booking flow | In-app real-time chat (v2 via Supabase Realtime) |
| Operator registration + dashboard | Live GPS tracking |
| Django Admin panel (operator/booking mgmt) | AI-powered pricing |
| Cashfree payment integration | EMI/Pay-later |
| Ratings & reviews | Multi-city expansion |
| WhatsApp contact integration | Bulk booking dashboard |
| Hindi + English bilingual | Operator mobile app (they use web) |
| OTP-based authentication | Social login (Google, Facebook) |
| SMS notifications (via n8n + MSG91) | Push notifications |
| Document upload + manual verification | AI document verification (v2 — Azure AI ready) |

---

## 2. FINAL TECH STACK

### Backend: Django + Django REST Framework (FINALIZED)

**Why Django is the right choice for a solo developer:**

```
✅ Built-in Admin Panel — saves 2+ weeks of development
   → Operator approval, booking management, user management — ALL FREE
   → Customize with django-jazzmin for modern admin UI

✅ Django ORM — auto migrations, no raw SQL needed
   → Define models in Python → Django creates tables automatically

✅ Django REST Framework (DRF) — fastest way to build REST APIs
   → Serializers, ViewSets, Pagination, Filtering — all built-in
   → ModelViewSet: Full CRUD in ~20 lines of code

✅ Security — CSRF, XSS, SQL injection protection out-of-the-box

✅ v2 Real-time Chat — NOT a problem!
   → Use Supabase Realtime (already in stack) for WebSocket
   → Django saves message to Supabase → Supabase pushes to client
   → No Django Channels or Socket.io needed
```

### Hosting: Heroku ($320 Free Credits)

```
Heroku Advantages:
+ One-command deploy: git push heroku main
+ Auto-scaling (no DevOps needed)
+ Free PostgreSQL add-on (Heroku Postgres) — backup option
+ No sleep/cold start issues (Eco dynos stay warm with $5/mo)
+ Built-in logs, monitoring
+ CI/CD via GitHub integration
+ $320 credits ≈ 12-16 months of Eco dynos ($5/mo each)

Heroku Cost with $320 Credits:
├── Web Dyno (Django): $5/month (Eco)
├── Worker Dyno (background tasks): $5/month (if needed later)
├── Heroku Postgres (Mini): $5/month (backup, or primary if Supabase limits hit)
└── Total: $5-15/month → $320 covers 21-64 months!
```

---

### Complete Tech Stack (FINALIZED)

| Layer | Technology | Purpose | Cost |
|---|---|---|---|
| **Frontend** | Next.js 14 (App Router) + Tailwind CSS | Customer website + PWA | ₹0 (Vercel free) |
| **Backend** | Django 5 + Django REST Framework | REST API + Admin Panel | ₹0 (Heroku $320 credits) |
| **Database** | Supabase (PostgreSQL) | All data storage | ₹0 (free tier: 500MB, 50K auth users) |
| **Authentication** | Supabase Auth | Phone OTP login, session management | ₹0 (included in Supabase free) |
| **Image Storage** | Cloudinary | Bus photos, document uploads (auto-optimized) | ₹0 (free: 25GB storage, 25GB BW) |
| **Payments** | Cashfree Payment Gateway | UPI, cards, net banking, payouts | 1.95% per transaction (no setup fee) |
| **SMS/OTP** | MSG91 (via n8n) | Booking confirmations, OTP | ~₹1,500 (5000 SMS) |
| **Maps** | Leaflet.js + OpenStreetMap | Location picker, distance calc | ₹0 (completely free, unlimited) |
| **Automation** | n8n (self-hosted) | Background workflows, notifications | ₹0 (self-hosted) |
| **AI/OCR** | Azure AI (Document Intelligence) | Auto-verify operator documents (v2) | ₹0 ($100 Azure credits) |
| **Real-time (v2)** | Supabase Realtime | Chat, live notifications | ₹0 (included in Supabase free) |
| **Analytics** | Google Analytics / Plausible | User behavior tracking | ₹0 |

---

## 3. SYSTEM ARCHITECTURE

```
                    ┌──────────────────────────────┐
                    │        USERS (Browser)        │
                    │    Customer / Operator / Admin │
                    └─────────────┬────────────────┘
                                  │ HTTPS
                    ┌─────────────▼────────────────┐
                    │     Next.js Frontend (PWA)    │
                    │        Vercel (Free)          │
                    │                               │
                    │  • Customer Pages             │
                    │  • Operator Dashboard         │
                    │  • Admin Panel (custom)        │
                    │  • Hindi/English Toggle       │
                    └─────────────┬────────────────┘
                                  │ REST API calls
                    ┌─────────────▼────────────────┐
                    │   Django + DRF Backend        │
                    │   Heroku ($320 credits)       │
                    │                               │
                    │  • REST API (DRF ViewSets)    │
                    │  • Django Admin Panel         │
                    │  • Booking engine              │
                    │  • Payment processing          │
                    │  • File upload handling        │
                    └──┬────┬────┬────┬────┬───────┘
                       │    │    │    │    │
          ┌────────────▼┐ ┌▼────▼┐ ┌▼────▼──┐ ┌──────┐
          │  Supabase   │ │Cloud-│ │Cashfree│ │ n8n  │
          │  (Postgres) │ │inary │ │Payment │ │Auto- │
          │  + Auth     │ │Images│ │Gateway │ │mation│
          │             │ │      │ │        │ │      │
          │• users      │ │• bus │ │• UPI   │ │• SMS │
          │• buses      │ │  pho-│ │• cards │ │• mail│
          │• bookings   │ │  tos │ │• net   │ │• cron│
          │• reviews    │ │• docs│ │  bank  │ │• docs│
          │• documents  │ │      │ │• payout│ │      │
          │• payments   │ │      │ │  to ops│ │      │
          └─────────────┘ └──────┘ └────────┘ └──┬───┘
                                                  │
                                          ┌───────▼──────┐
                                          │   MSG91 SMS  │
                                          │   Azure AI   │
                                          │  (via n8n)   │
                                          └──────────────┘
```

### Request Flow Example (Customer Books a Bus)

```
1. Customer → Next.js: "Show buses for Jaipur→Bharatpur, Feb 25, 40 pax"
2. Next.js → Backend API: GET /api/buses/search?from=jaipur&to=bharatpur&date=2026-02-25&pax=40
3. Backend → Supabase: SQL query (available buses, not booked on that date)
4. Supabase → Backend: Returns 8 matching buses
5. Backend → Next.js: JSON response with bus details
6. Next.js → Customer: Shows bus cards with photos (from Cloudinary CDN)
7. Customer selects bus → Next.js: Shows booking form
8. Customer confirms → Backend API: POST /api/bookings
9. Backend → Supabase: INSERT booking (status: pending_payment)
10. Backend → Cashfree: Create payment order
11. Cashfree → Customer: Payment page (UPI/card)
12. Customer pays → Cashfree webhook → Backend: Payment confirmed
13. Backend → Supabase: UPDATE booking (status: confirmed)
14. Backend → n8n webhook: Trigger "booking_confirmed" workflow
15. n8n → MSG91: Send SMS to customer + operator
16. n8n → Email: Send booking confirmation email
```

---

## 4. DATABASE SCHEMA

### Entity Relationship Diagram (Text)

```
users
  ├── 1:N → buses (operator owns buses)
  ├── 1:N → bookings (customer makes bookings)
  ├── 1:N → reviews (customer writes reviews)
  └── 1:N → documents (operator uploads documents)

buses
  ├── N:1 → users (owned by operator)
  ├── 1:N → bus_photos (multiple photos per bus)
  ├── 1:N → bus_amenities (amenities list)
  ├── 1:N → bookings (bookings for this bus)
  ├── 1:N → reviews (reviews for this bus)
  └── 1:N → availability_blocks (dates blocked)

bookings
  ├── N:1 → users (booked by customer)
  ├── N:1 → buses (which bus)
  ├── 1:1 → payments (payment record)
  └── 1:1 → reviews (review after trip)
```

### Table Definitions

#### `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(15) UNIQUE NOT NULL,       -- +919829012345
    name            VARCHAR(100),
    email           VARCHAR(255),
    role            VARCHAR(20) NOT NULL DEFAULT 'customer',  -- 'customer', 'operator', 'admin'
    avatar_url      TEXT,
    
    -- Operator-specific fields
    business_name   VARCHAR(200),                      -- "Yaduvanshi Travels"
    business_type   VARCHAR(50),                       -- 'individual', 'company'
    gst_number      VARCHAR(20),
    pan_number      VARCHAR(15),
    bank_account    VARCHAR(20),
    bank_ifsc       VARCHAR(15),
    bank_name       VARCHAR(100),
    address         TEXT,
    city            VARCHAR(100),
    
    -- Operator verification
    is_verified     BOOLEAN DEFAULT FALSE,
    verified_at     TIMESTAMPTZ,
    verification_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
    rejection_reason TEXT,
    
    -- Platform data
    rating_avg      DECIMAL(2,1) DEFAULT 0.0,
    rating_count    INTEGER DEFAULT 0,
    total_bookings  INTEGER DEFAULT 0,
    
    -- Subscription (for operators)
    subscription_tier VARCHAR(20) DEFAULT 'free',      -- 'free', 'pro', 'enterprise'
    subscription_expires_at TIMESTAMPTZ,
    commission_rate DECIMAL(4,2) DEFAULT 10.00,        -- percentage
    
    -- Meta
    preferred_language VARCHAR(5) DEFAULT 'hi',        -- 'hi', 'en'
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_city ON users(city);
```

#### `buses`
```sql
CREATE TABLE buses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Basic info
    name            VARCHAR(200) NOT NULL,             -- "Deluxe AC Coach"
    description     TEXT,
    bus_type        VARCHAR(50) NOT NULL,              -- 'mini_bus', 'medium_bus', 'luxury_coach', 'tempo_traveller'
    seating_capacity INTEGER NOT NULL,                 -- 17, 25, 30, 40, 50
    
    -- Vehicle details
    registration_number VARCHAR(20) NOT NULL,          -- RJ14 SA 1234
    make_model      VARCHAR(100),                      -- "Tata Starbus", "Force Traveller"
    manufacture_year INTEGER,
    ac_type         VARCHAR(20) NOT NULL,              -- 'ac', 'non_ac', 'both'
    fuel_type       VARCHAR(20) DEFAULT 'diesel',      -- 'diesel', 'cng', 'electric'
    
    -- Pricing
    price_per_km    DECIMAL(8,2) NOT NULL,             -- ₹18.50/km
    base_price      DECIMAL(10,2),                     -- Minimum charge ₹3,000
    driver_charge   DECIMAL(10,2) DEFAULT 0,           -- ₹500/day
    night_charge    DECIMAL(10,2) DEFAULT 0,           -- ₹1,000/night halt
    
    -- Location
    base_city       VARCHAR(100) NOT NULL DEFAULT 'Jaipur',
    base_area       VARCHAR(100),                      -- "Mansarovar", "Vaishali Nagar"
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    is_approved     BOOLEAN DEFAULT FALSE,
    approval_status VARCHAR(20) DEFAULT 'pending',     -- 'pending', 'approved', 'rejected'
    
    -- Ratings
    rating_avg      DECIMAL(2,1) DEFAULT 0.0,
    rating_count    INTEGER DEFAULT 0,
    total_trips     INTEGER DEFAULT 0,
    
    -- Meta
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_buses_operator ON buses(operator_id);
CREATE INDEX idx_buses_city ON buses(base_city);
CREATE INDEX idx_buses_type ON buses(bus_type);
CREATE INDEX idx_buses_capacity ON buses(seating_capacity);
CREATE INDEX idx_buses_active ON buses(is_active, is_approved);
```

#### `bus_photos`
```sql
CREATE TABLE bus_photos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bus_id          UUID NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
    photo_url       TEXT NOT NULL,                     -- Cloudinary URL
    photo_type      VARCHAR(30) NOT NULL,              -- 'exterior_front', 'exterior_side', 'interior', 'seats', 'dashboard', 'other'
    display_order   INTEGER DEFAULT 0,
    is_primary      BOOLEAN DEFAULT FALSE,             -- Main display photo
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bus_photos_bus ON bus_photos(bus_id);
```

#### `bus_amenities`
```sql
CREATE TABLE bus_amenities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bus_id          UUID NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
    amenity         VARCHAR(50) NOT NULL,              -- 'music_system', 'pushback_seats', 'charging_points', 'first_aid', 'fire_extinguisher', 'reading_lights', 'luggage_space', 'water_bottles', 'dj_system', 'wifi', 'tv_screen'
    UNIQUE(bus_id, amenity)
);

CREATE INDEX idx_bus_amenities_bus ON bus_amenities(bus_id);
```

#### `availability_blocks`
```sql
-- Dates when bus is NOT available (blocked by operator or booked)
CREATE TABLE availability_blocks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bus_id          UUID NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
    blocked_date    DATE NOT NULL,
    block_reason    VARCHAR(50) NOT NULL,              -- 'booked_platform', 'booked_external', 'maintenance', 'personal'
    booking_id      UUID REFERENCES bookings(id),      -- If blocked due to platform booking
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(bus_id, blocked_date)
);

CREATE INDEX idx_availability_bus_date ON availability_blocks(bus_id, blocked_date);
```

#### `bookings`
```sql
CREATE TABLE bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_number  VARCHAR(20) UNIQUE NOT NULL,       -- "BK-20260225-001"
    
    -- Parties
    customer_id     UUID NOT NULL REFERENCES users(id),
    operator_id     UUID NOT NULL REFERENCES users(id),
    bus_id          UUID NOT NULL REFERENCES buses(id),
    
    -- Trip details
    trip_type       VARCHAR(20) NOT NULL,              -- 'one_way', 'round_trip', 'multi_day'
    pickup_location TEXT NOT NULL,                     -- "Mansarovar, Jaipur"
    pickup_lat      DECIMAL(10,7),
    pickup_lng      DECIMAL(10,7),
    drop_location   TEXT NOT NULL,                     -- "Bharatpur"
    drop_lat        DECIMAL(10,7),
    drop_lng        DECIMAL(10,7),
    pickup_date     DATE NOT NULL,
    pickup_time     TIME NOT NULL,
    return_date     DATE,                              -- For round_trip / multi_day
    passenger_count INTEGER NOT NULL,
    purpose         VARCHAR(50),                       -- 'wedding', 'religious', 'family_trip', 'corporate', 'school_tour', 'other'
    special_requests TEXT,
    
    -- Distance & route
    estimated_km    DECIMAL(8,2),
    estimated_route TEXT,                              -- "Via NH48, Dausa"
    
    -- Pricing breakdown
    base_amount     DECIMAL(10,2) NOT NULL,            -- Bus rental charge
    driver_charge   DECIMAL(10,2) DEFAULT 0,
    night_charge    DECIMAL(10,2) DEFAULT 0,
    toll_estimate   DECIMAL(10,2) DEFAULT 0,
    platform_fee    DECIMAL(10,2) DEFAULT 0,           -- Service fee
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_amount    DECIMAL(10,2) NOT NULL,
    
    -- Commission
    commission_rate DECIMAL(4,2) NOT NULL,             -- 10.00
    commission_amount DECIMAL(10,2) NOT NULL,          -- ₹1,500
    operator_payout DECIMAL(10,2) NOT NULL,            -- ₹13,500
    
    -- Status
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- Statuses: 'pending' → 'confirmed' → 'in_progress' → 'completed'
    --           'pending' → 'cancelled_by_customer'
    --           'confirmed' → 'cancelled_by_operator'
    --           'pending' → 'expired' (operator didn't respond in time)
    
    -- Operator response
    operator_response VARCHAR(20),                     -- 'accepted', 'rejected'
    operator_response_at TIMESTAMPTZ,
    rejection_reason TEXT,
    
    -- Payment
    payment_mode    VARCHAR(20) NOT NULL,              -- 'online_full', 'online_advance', 'pay_driver'
    payment_status  VARCHAR(20) DEFAULT 'pending',     -- 'pending', 'advance_paid', 'fully_paid', 'refunded'
    advance_amount  DECIMAL(10,2) DEFAULT 0,
    
    -- Cancellation
    cancelled_at    TIMESTAMPTZ,
    cancellation_reason TEXT,
    refund_amount   DECIMAL(10,2) DEFAULT 0,
    
    -- Completion
    completed_at    TIMESTAMPTZ,
    operator_payout_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'paid'
    operator_payout_at TIMESTAMPTZ,
    
    -- Meta
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_operator ON bookings(operator_id);
CREATE INDEX idx_bookings_bus ON bookings(bus_id);
CREATE INDEX idx_bookings_date ON bookings(pickup_date);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_number ON bookings(booking_number);
```

#### `payments`
```sql
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID NOT NULL REFERENCES bookings(id),
    
    -- Cashfree details
    cf_order_id          VARCHAR(100),
    cf_payment_id        VARCHAR(100),
    cf_payment_session_id VARCHAR(255),
    
    -- Amount
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'INR',
    payment_type    VARCHAR(20) NOT NULL,              -- 'advance', 'full', 'remaining', 'refund'
    payment_method  VARCHAR(30),                       -- 'upi', 'card', 'netbanking', 'wallet'
    
    -- Status
    status          VARCHAR(20) NOT NULL DEFAULT 'created',  -- 'created', 'authorized', 'captured', 'failed', 'refunded'
    
    -- Meta
    metadata        JSONB,                             -- Additional payment data from Cashfree
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_booking ON payments(booking_id);
CREATE INDEX idx_payments_cf ON payments(cf_order_id);
```

#### `reviews`
```sql
CREATE TABLE reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID UNIQUE NOT NULL REFERENCES bookings(id),
    customer_id     UUID NOT NULL REFERENCES users(id),
    bus_id          UUID NOT NULL REFERENCES buses(id),
    operator_id     UUID NOT NULL REFERENCES users(id),
    
    -- Rating (1-5)
    rating_overall  INTEGER NOT NULL CHECK (rating_overall BETWEEN 1 AND 5),
    rating_cleanliness INTEGER CHECK (rating_cleanliness BETWEEN 1 AND 5),
    rating_punctuality INTEGER CHECK (rating_punctuality BETWEEN 1 AND 5),
    rating_driver   INTEGER CHECK (rating_driver BETWEEN 1 AND 5),
    rating_value    INTEGER CHECK (rating_value BETWEEN 1 AND 5),
    
    -- Review text
    review_text     TEXT,
    
    -- Photos uploaded by customer
    photo_urls      TEXT[],                            -- Array of Cloudinary URLs
    
    -- Admin moderation
    is_approved     BOOLEAN DEFAULT TRUE,
    is_flagged      BOOLEAN DEFAULT FALSE,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reviews_bus ON reviews(bus_id);
CREATE INDEX idx_reviews_operator ON reviews(operator_id);
```

#### `operator_documents`
```sql
CREATE TABLE operator_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bus_id          UUID REFERENCES buses(id) ON DELETE CASCADE,  -- NULL for owner-level docs
    
    document_type   VARCHAR(50) NOT NULL,
    -- Owner docs: 'aadhar', 'pan', 'bank_proof'
    -- Bus docs: 'rc', 'fitness_certificate', 'permit', 'insurance', 'puc', 'road_tax'
    -- Driver docs: 'driver_license', 'driver_aadhar', 'police_verification'
    -- Company docs: 'gst_certificate', 'trade_license', 'company_registration'
    
    document_url    TEXT NOT NULL,                     -- Cloudinary URL (private)
    document_number VARCHAR(50),                      -- RC number, license number etc.
    expiry_date     DATE,                             -- For fitness, permit, insurance
    
    verification_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
    verified_by     UUID REFERENCES users(id),
    verified_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_user ON operator_documents(user_id);
CREATE INDEX idx_documents_bus ON operator_documents(bus_id);
CREATE INDEX idx_documents_expiry ON operator_documents(expiry_date);
```

#### `coupons`
```sql
CREATE TABLE coupons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(20) UNIQUE NOT NULL,       -- "FIRST1000"
    description     TEXT,
    discount_type   VARCHAR(10) NOT NULL,              -- 'flat', 'percentage'
    discount_value  DECIMAL(10,2) NOT NULL,            -- 1000 (flat) or 10 (%)
    max_discount    DECIMAL(10,2),                     -- Cap for percentage discounts
    min_booking     DECIMAL(10,2) DEFAULT 0,           -- Minimum booking value
    usage_limit     INTEGER,                           -- Total uses allowed
    used_count      INTEGER DEFAULT 0,
    per_user_limit  INTEGER DEFAULT 1,
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `coupon_usage`
```sql
CREATE TABLE coupon_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupon_id       UUID NOT NULL REFERENCES coupons(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    booking_id      UUID NOT NULL REFERENCES bookings(id),
    discount_applied DECIMAL(10,2) NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(coupon_id, user_id, booking_id)
);
```

#### `notifications`
```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    type            VARCHAR(50) NOT NULL,              -- 'booking_confirmed', 'booking_cancelled', 'new_review', 'payment_received', 'document_verified'
    title           VARCHAR(200) NOT NULL,
    message         TEXT NOT NULL,
    is_read         BOOLEAN DEFAULT FALSE,
    metadata        JSONB,                             -- { booking_id, bus_id, etc. }
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
```

---

## 5. API ENDPOINTS

### Authentication
```
POST   /api/auth/send-otp         → Send OTP to phone number
POST   /api/auth/verify-otp       → Verify OTP, return JWT token
POST   /api/auth/refresh           → Refresh JWT token
GET    /api/auth/me                → Get current user profile
PUT    /api/auth/profile           → Update profile
POST   /api/auth/logout            → Invalidate token
```

### Buses (Public)
```
GET    /api/buses/search           → Search available buses
       Query: ?from=jaipur&to=bharatpur&date=2026-02-25&pax=40&type=ac&sort=price
       Response: Paginated list of available buses with photos and ratings

GET    /api/buses/:id              → Get bus details (photos, amenities, reviews)
GET    /api/buses/:id/reviews      → Get bus reviews (paginated)
GET    /api/buses/:id/availability → Get availability calendar (next 90 days)
```

### Buses (Operator - Protected)
```
POST   /api/operator/buses              → Add new bus
PUT    /api/operator/buses/:id          → Update bus details
DELETE /api/operator/buses/:id          → Deactivate bus
POST   /api/operator/buses/:id/photos   → Upload bus photos (Cloudinary)
DELETE /api/operator/buses/:id/photos/:photoId → Delete photo
PUT    /api/operator/buses/:id/pricing  → Update pricing
POST   /api/operator/buses/:id/amenities → Set amenities
POST   /api/operator/buses/:id/block-dates → Block dates
DELETE /api/operator/buses/:id/block-dates → Unblock dates
GET    /api/operator/buses/:id/calendar → Get calendar view
```

### Bookings (Customer)
```
POST   /api/bookings                    → Create booking
       Body: { bus_id, pickup_location, drop_location, pickup_date, pickup_time, 
               passenger_count, trip_type, purpose, payment_mode }
GET    /api/bookings                    → List my bookings (customer)
GET    /api/bookings/:id                → Booking details
PUT    /api/bookings/:id/cancel         → Cancel booking
POST   /api/bookings/:id/review         → Submit review
```

### Bookings (Operator)
```
GET    /api/operator/bookings           → List incoming bookings
PUT    /api/operator/bookings/:id/accept → Accept booking
PUT    /api/operator/bookings/:id/reject → Reject booking (with reason)
PUT    /api/operator/bookings/:id/complete → Mark trip completed
```

### Payments
```
POST   /api/payments/create-order       → Create Cashfree order
POST   /api/payments/verify             → Verify payment (webhook + client)
GET    /api/payments/:bookingId         → Get payment details
POST   /api/payments/webhook            → Cashfree webhook (server-to-server)
```

### Operator Dashboard
```
GET    /api/operator/dashboard          → Stats (total bookings, revenue, rating)
GET    /api/operator/earnings           → Earnings breakdown
GET    /api/operator/documents          → List uploaded documents
POST   /api/operator/documents          → Upload document
```

### Admin
```
GET    /api/admin/operators             → List all operators (filter by verification status)
PUT    /api/admin/operators/:id/verify  → Approve/reject operator
GET    /api/admin/bookings              → All bookings (filterable)
GET    /api/admin/dashboard             → Platform stats
GET    /api/admin/documents/:id         → View operator document
PUT    /api/admin/documents/:id/verify  → Approve/reject document
GET    /api/admin/reviews               → All reviews (for moderation)
PUT    /api/admin/reviews/:id           → Moderate review (approve/flag)
GET    /api/admin/coupons               → List coupons
POST   /api/admin/coupons               → Create coupon
PUT    /api/admin/coupons/:id           → Update coupon
```

### Notifications
```
GET    /api/notifications               → List user notifications
PUT    /api/notifications/:id/read      → Mark as read
PUT    /api/notifications/read-all      → Mark all as read
```

### Utility
```
GET    /api/locations/search            → Search locations (autocomplete)
GET    /api/locations/distance          → Calculate distance between two points
GET    /api/price/estimate              → Get price estimate for a route
```

---

## 6. FEATURE SPECIFICATIONS

### 6.1 Customer Search & Booking Flow

**Search Page:**
```
Input Fields:
├── Pickup City/Area (autocomplete, default: Jaipur)
├── Drop City/Area (autocomplete)
├── Pickup Date (date picker, min: tomorrow)
├── Return Date (optional, for round trips)
├── Passenger Count (number input, min: 7)
├── Trip Type (one-way / round-trip / multi-day)
└── [Search Button]

Filters (on results page):
├── Bus Type: Mini Bus, Tempo Traveller, Medium Bus, Luxury Coach
├── AC/Non-AC
├── Price Range: Slider ₹3,000 - ₹50,000
├── Rating: 4+, 3+, any
├── Amenities: Checkboxes
└── Sort: Price Low→High, Rating, Popularity
```

**Results Page:**
```
Bus Card:
├── Primary Photo (from Cloudinary, 300x200 optimized)
├── Bus Name + Type badge
├── Operator Name + Verified badge ✓
├── Rating: ⭐ 4.5 (120 reviews)
├── Capacity: 40 seats
├── Amenities icons: ❄️ AC | 🎵 Music | 🔌 Charging
├── Price: ₹15,000 (breakdown on hover)
├── Availability indicator: ✅ Instant Book / ⏰ Request Booking
└── [View Details] [Book Now]
```

**Bus Detail Page:**
```
├── Photo Gallery (6-8 images, swipeable)
├── Bus Specifications
│   ├── Make/Model, Year, Capacity
│   ├── AC type, Fuel type
│   └── Registration: RJ14 XX ****  (partially hidden)
├── Amenities List (with icons)
├── Pricing Breakdown
│   ├── Base: ₹X per km × estimated Y km = ₹Z
│   ├── Driver charge: ₹500
│   ├── Estimated toll: ₹200
│   └── Total: ₹15,000
├── Operator Info
│   ├── Name, Verified badge
│   ├── Member since: 2020
│   ├── Total trips: 250
│   └── [WhatsApp Contact] (pre-booking query only)
├── Reviews (latest 5, "See all" link)
├── Cancellation Policy
└── [Book This Bus] button
```

**Booking Confirmation Page:**
```
├── Booking Summary
│   ├── Route: Jaipur → Bharatpur
│   ├── Date: Feb 25, 2026, 10:00 AM
│   ├── Bus: Deluxe AC Coach (40-seater)
│   ├── Passengers: 40
│   └── Total: ₹15,000
├── Payment Options
│   ├── ○ Pay Full Online (₹15,000) — Get ₹199 free trip insurance!
│   ├── ○ Pay Advance (₹3,000) — Remaining to driver
│   └── ○ Pay Driver (₹15,000 cash) — ₹500 booking fee online
├── Apply Coupon: [________] [Apply]
├── Special Requests: [textarea]
└── [Confirm & Pay] button
```

### 6.2 Operator Dashboard

**Dashboard Home:**
```
Stats Cards:
├── Total Bookings: 45
├── This Month Revenue: ₹2,40,000
├── Average Rating: 4.6 ⭐
├── Pending Requests: 3
└── Upcoming Trips: 5

Quick Actions:
├── [Add New Bus]
├── [View Calendar]
├── [Manage Documents]
└── [View Earnings]
```

**My Buses:**
```
List of operator's buses:
├── Bus Card
│   ├── Photo thumbnail
│   ├── Name + Registration
│   ├── Status: ✅ Active / ⏰ Pending Approval / ❌ Rejected
│   ├── Rating + Trip count
│   ├── Next booking date
│   └── [Edit] [Calendar] [Deactivate]
└── [+ Add New Bus]
```

**Booking Management:**
```
Tabs: All | Pending | Upcoming | Completed | Cancelled

Booking Row:
├── Booking #BK-20260225-001
├── Customer: Rajesh K. (★ verified)
├── Route: Jaipur → Bharatpur
├── Date: Feb 25, 10:00 AM
├── Amount: ₹15,000 (Your payout: ₹13,500)
├── Status badge
├── [Accept] [Reject] (for pending)
└── [Mark Complete] (for upcoming, on trip day)
```

**Availability Calendar:**
```
Monthly calendar view:
├── Green dates: Available
├── Red dates: Booked (platform)
├── Orange dates: Blocked (external booking / personal)
├── Click date → Block/Unblock with reason
└── Bulk block: Select date range → Block
```

### 6.3 Admin Panel

**If Django:** Auto-generated admin panel covers 80% of needs. Customize remaining 20% with django-jazzmin.

```
Django Admin (/admin/) handles:
├── Operator Management: View/approve/reject operators, view documents
├── Bus Management: Approve/reject buses, view photos
├── Booking Management: All bookings with filters (status, date, city)
├── Payment Records: View payment status, refund tracking
├── Review Moderation: Approve/flag/remove reviews
└── Coupon Management: Create/edit/deactivate coupons

Additional Custom Admin Page (in Next.js frontend):
├── Visual Dashboard: Charts, today's stats, revenue trends
└── This is optional — Django admin covers all functional needs
```

---

## 7. USER ROLES & PERMISSIONS

```
Role: CUSTOMER
├── Search buses
├── Create bookings
├── Make payments
├── Cancel own bookings
├── Write reviews (for completed bookings only)
├── View own booking history
├── Contact operator via WhatsApp (after booking)
└── Update own profile

Role: OPERATOR
├── All CUSTOMER permissions +
├── Add / edit / deactivate own buses
├── Upload bus photos and documents
├── Manage availability calendar
├── Accept / reject booking requests
├── Mark trips as completed
├── View own earnings and payouts
└── Cannot: See other operators' data

Role: ADMIN
├── All permissions +
├── Verify / reject operators
├── Verify / reject documents
├── View all bookings
├── Issue refunds
├── Moderate reviews
├── Manage coupons
├── View platform analytics
├── Suspend users
└── Manage commission rates
```

### Row-Level Security (Supabase RLS)
```sql
-- Customers can only see their own bookings
CREATE POLICY "Customers see own bookings" ON bookings
    FOR SELECT USING (auth.uid() = customer_id);

-- Operators can only see bookings for their buses
CREATE POLICY "Operators see own bookings" ON bookings
    FOR SELECT USING (auth.uid() = operator_id);

-- Operators can only edit their own buses
CREATE POLICY "Operators edit own buses" ON buses
    FOR ALL USING (auth.uid() = operator_id);

-- Admins can see everything
CREATE POLICY "Admin full access" ON bookings
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );
```

---

## 8. UI/UX SCREENS

### Screen List (Next.js Pages)

```
Public Pages:
├── /                          → Landing page (hero + search + how it works)
├── /search                    → Bus search results
├── /bus/[id]                  → Bus detail page
├── /login                     → Phone OTP login
├── /about                     → About us
├── /contact                   → Contact page
└── /terms, /privacy           → Legal pages

Customer Pages (Protected):
├── /bookings                  → My bookings list
├── /bookings/[id]             → Booking detail
├── /bookings/[id]/review      → Write review
├── /profile                   → My profile + settings
└── /checkout/[bookingId]      → Payment page

Operator Pages (Protected):
├── /operator/dashboard        → Dashboard home
├── /operator/buses            → My buses list
├── /operator/buses/new        → Add new bus
├── /operator/buses/[id]/edit  → Edit bus
├── /operator/buses/[id]/photos → Manage photos
├── /operator/buses/[id]/calendar → Availability calendar
├── /operator/bookings         → Incoming bookings
├── /operator/earnings         → Earnings & payouts
├── /operator/documents        → Upload documents
├── /operator/profile          → Business profile
└── /operator/register         → Operator registration flow

Admin Pages (Protected):
├── /admin/dashboard           → Platform overview
├── /admin/operators           → Operator management
├── /admin/operators/[id]      → Operator detail + verification
├── /admin/bookings            → All bookings
├── /admin/reviews             → Review moderation
├── /admin/coupons             → Coupon management
└── /admin/settings            → Platform settings
```

### Responsive Design Breakpoints
```
Mobile (primary):  320px - 768px  → Single column, touch-friendly
Tablet:            768px - 1024px → Two column where appropriate
Desktop:           1024px+        → Full layout
```

---

## 9. N8N AUTOMATION WORKFLOWS

### Workflow 1: Booking Confirmation
```
Trigger: Webhook from backend (POST /n8n/booking-confirmed)
Payload: { booking_id, customer_phone, customer_name, operator_phone, 
           bus_name, pickup_date, pickup_time, route, amount }

Actions:
1. Send SMS to Customer (MSG91):
   "Hi {name}, your bus booking #{booking_number} is confirmed!
    Bus: {bus_name}
    Date: {pickup_date} at {pickup_time}
    Route: {route}
    Amount: ₹{amount}
    Support: +91XXXXXXXXXX"

2. Send SMS to Operator (MSG91):
   "New booking received! #{booking_number}
    Date: {pickup_date} at {pickup_time}
    Route: {route}
    Passengers: {pax}
    Payout: ₹{operator_payout}
    Accept in app within 1 hour."

3. Insert notification in Supabase (for in-app notification)
```

### Workflow 2: Operator Response Timeout
```
Trigger: Cron (every 15 minutes)

Actions:
1. Query Supabase: SELECT bookings WHERE status = 'pending' AND created_at < NOW() - INTERVAL '2 hours'
2. For each expired booking:
   a. Update status to 'expired'
   b. Send SMS to customer: "Sorry, operator didn't respond. We'll find you another bus."
   c. Send SMS to operator: "You missed a booking request. Frequent misses may affect your ranking."
   d. Refund advance payment (if any) via Cashfree API
```

### Workflow 3: Daily Calendar Reminder
```
Trigger: Cron (every day at 9:00 AM)

Actions:
1. Query Supabase: SELECT operators WHERE has_active_buses = true
2. Send SMS to each: "Good morning! Please update your bus availability for the next 7 days on the app."
```

### Workflow 4: Review Request (Post-Trip)
```
Trigger: Cron (every day at 10:00 AM)

Actions:
1. Query Supabase: SELECT bookings WHERE status = 'completed' 
   AND completed_at BETWEEN 24 AND 48 hours ago
   AND NOT EXISTS (SELECT 1 FROM reviews WHERE booking_id = bookings.id)
2. Send SMS to customer:
   "How was your trip with {bus_name}? Rate your experience & get ₹100 off next booking! {link}"
```

### Workflow 5: Document Expiry Alert
```
Trigger: Cron (every day at 8:00 AM)

Actions:
1. Query Supabase: SELECT operator_documents WHERE expiry_date BETWEEN NOW() AND NOW() + 30 days
2. For each expiring document:
   Send SMS to operator: "Your {document_type} for bus {registration} expires on {expiry_date}. 
   Please renew and upload the new document."
```

### Workflow 6: New Operator Registration
```
Trigger: Webhook from backend (POST /n8n/new-operator)

Actions:
1. Send SMS to operator: "Welcome! Your registration is under review. We'll verify your documents within 48 hours."
2. Send Email/SMS to Admin: "New operator registered: {business_name}. Review at {admin_url}"
3. Insert notification for admin in Supabase
```

### Workflow 7: Weekly Admin Report
```
Trigger: Cron (every Monday at 8:00 AM)

Actions:
1. Query Supabase: Aggregate stats for past week
   - New bookings count + GMV
   - New operators registered
   - Average rating
   - Cancellation rate
   - Top performing operator
2. Format HTML email
3. Send to admin email
```

### Workflow 8: Payment Payout Reminder
```
Trigger: Cron (every day at 11:00 AM)

Actions:
1. Query Supabase: SELECT bookings WHERE status = 'completed' 
   AND operator_payout_status = 'pending' AND completed_at < NOW() - 3 days
2. Alert admin: "Pending operator payouts: {count} bookings, total ₹{amount}"
```

---

## 10. PAYMENT FLOW

### Flow 1: Full Online Payment
```
Customer → Selects "Pay Full Online"
  → Backend creates Cashfree Order (₹15,000)
  → Customer completes payment (UPI/Card/NetBanking)
  → Cashfree sends webhook to backend
  → Backend verifies payment signature
  → Booking confirmed
  → After trip + 3 days: Admin initiates payout to operator (₹13,500)
    (via Cashfree Payouts API or manual bank transfer)
  → Platform keeps commission (₹1,500)
```

### Flow 2: Advance + Cash
```
Customer → Selects "Pay Advance" 
  → Backend creates Cashfree Order (₹3,000 advance)
  → Customer pays ₹3,000 online
  → Booking confirmed
  → Day of trip: Customer pays ₹12,000 cash to driver
  → Monthly: Operator pays commission (₹1,500) to platform
     OR deducted from security deposit
```

### Flow 3: Booking Fee Only (Pay Driver)
```
Customer → Selects "Pay Driver"
  → Backend creates Cashfree Order (₹500 booking fee — non-refundable)
  → Customer pays ₹500 online
  → Booking confirmed
  → Day of trip: Customer pays ₹15,000 cash to driver
  → Monthly: Operator pays commission (₹1,500) to platform
```

### Cancellation & Refund Policy
```
Cancellation by Customer:
├── > 72 hours before trip: 90% refund (10% cancellation fee)
├── 24-72 hours before trip: 50% refund
├── < 24 hours before trip: No refund
└── Refund processed within 5-7 business days via Cashfree

Cancellation by Operator:
├── Any time: 100% refund to customer
├── Operator penalty: ₹3,000 (from security deposit)
├── Strike on operator profile
└── 3 cancellations = Account review/suspension
```

### Cashfree Integration Points
```
Backend (Django):
1. cashfree_sdk → Create order (POST /pg/orders)
2. Webhook handler (PAYMENT_SUCCESS, PAYMENT_FAILED)
3. Payment signature verification (using Cashfree secret key)
4. Refund initiation (POST /pg/orders/{order_id}/refunds)
5. Cashfree Payouts (for operator payouts — v2)

Frontend (Next.js):
1. Cashfree JS SDK (cashfree-js) → Drop-in payment component
2. Payment status callback handling
3. Success/failure redirect

Python Package: cashfree-pg (pip install cashfree-pg)

Environment Variables:
CASHFREE_APP_ID=your_app_id
CASHFREE_SECRET_KEY=your_secret_key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_ENVIRONMENT=PRODUCTION    # or SANDBOX for testing
```

---

## 11. INTERNATIONALIZATION (Hindi + English)

### Implementation Approach

**Use `next-intl` or `react-i18next` library**

```
Folder Structure:
/locales
├── en.json     → English translations
└── hi.json     → Hindi translations
```

### Sample Translation Keys
```json
// en.json
{
  "common": {
    "search": "Search",
    "book_now": "Book Now",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "login": "Login",
    "logout": "Logout"
  },
  "search": {
    "title": "Find the Perfect Bus",
    "from": "Pickup Location",
    "to": "Drop Location",
    "date": "Travel Date",
    "passengers": "Number of Passengers",
    "search_btn": "Search Buses",
    "no_results": "No buses available for this route and date"
  },
  "booking": {
    "confirmed": "Booking Confirmed!",
    "booking_id": "Booking ID",
    "total_amount": "Total Amount",
    "pay_online": "Pay Online",
    "pay_driver": "Pay Driver"
  }
}

// hi.json
{
  "common": {
    "search": "खोजें",
    "book_now": "अभी बुक करें",
    "cancel": "रद्द करें",
    "confirm": "पुष्टि करें",
    "login": "लॉगिन",
    "logout": "लॉगआउट"
  },
  "search": {
    "title": "सही बस खोजें",
    "from": "पिकअप स्थान",
    "to": "ड्रॉप स्थान",
    "date": "यात्रा की तारीख",
    "passengers": "यात्रियों की संख्या",
    "search_btn": "बस खोजें",
    "no_results": "इस रूट और तारीख के लिए कोई बस उपलब्ध नहीं है"
  },
  "booking": {
    "confirmed": "बुकिंग पक्की हो गई!",
    "booking_id": "बुकिंग आईडी",
    "total_amount": "कुल राशि",
    "pay_online": "ऑनलाइन भुगतान करें",
    "pay_driver": "ड्राइवर को भुगतान करें"
  }
}
```

### Language Selection
```
- Default: Hindi (hi) — majority Rajasthan users prefer Hindi
- Toggle: Globe icon 🌐 in header → switch language
- Stored in localStorage + user profile (if logged in)
- URL: /en/search or /hi/search (optional, for SEO)
```

### SMS Templates (Bilingual)
```
Hindi SMS (default):
"नमस्ते {name}! आपकी बस बुकिंग #{id} पक्की हो गई।
बस: {bus_name}
तारीख: {date}, {time}
किराया: ₹{amount}
सहायता: +91XXXXXXXXXX"

English SMS (if user preference = English):
"Hi {name}! Your bus booking #{id} is confirmed.
Bus: {bus_name}
Date: {date}, {time}
Amount: ₹{amount}
Support: +91XXXXXXXXXX"
```

---

## 12. PWA CONFIGURATION

### manifest.json
```json
{
  "name": "BusBook - Bus Rental Booking",
  "short_name": "BusBook",
  "description": "Book buses & mini-buses for weddings, tours, and trips",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#FF6B00",
  "orientation": "portrait",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### PWA Features for MVP
```
✅ Add to Home Screen prompt
✅ Offline fallback page ("No internet. Please check your connection.")
✅ Cached static assets (CSS, JS, icons)
✅ App-like navigation (no browser chrome)

❌ NOT in MVP: Background sync, push notifications (requires service worker complexity)
```

### Service Worker Strategy
```
- Use next-pwa package (auto-generates SW)
- Cache Strategy: Network First (for API calls) + Cache First (for images)
- Offline: Show cached booking history + "you're offline" banner
```

---

## 13. DEPLOYMENT PLAN

### Environment Setup

```
Environments:
├── Development (local)
│   ├── Frontend: localhost:3000 (Next.js dev server)
│   └── Backend: localhost:8000 (Django dev server)
│
├── Staging (for testing before launch)
│   ├── Frontend: staging.yourdomain.com (Vercel preview)
│   └── Backend: your-app-staging.herokuapp.com
│
└── Production
    ├── Frontend: www.yourdomain.com (Vercel)
    └── Backend: your-app.herokuapp.com (or api.yourdomain.com via custom domain)
```

### Environment Variables

```env
# Backend (Django .env / Heroku Config Vars)
DJANGO_SECRET_KEY=your-super-secret-django-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-app.herokuapp.com,api.yourdomain.com

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxxx
SUPABASE_SERVICE_KEY=eyJxxxxxx   # Server-side only, never expose to client

# Cashfree
CASHFREE_APP_ID=your_app_id
CASHFREE_SECRET_KEY=your_secret_key
CASHFREE_ENVIRONMENT=PRODUCTION

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=XXXXXXXXX
CLOUDINARY_API_SECRET=XXXXXXXXXXXXX

# MSG91 (used by n8n, but backend may also send OTP)
MSG91_AUTH_KEY=XXXXXXXXXX
MSG91_SENDER_ID=BUSBOK

# n8n Webhook URLs
N8N_WEBHOOK_BASE_URL=https://your-n8n-instance.com/webhook

# Database (Heroku auto-sets DATABASE_URL for Heroku Postgres)
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxxx
NEXT_PUBLIC_API_URL=https://your-app.herokuapp.com
NEXT_PUBLIC_CASHFREE_APP_ID=your_app_id
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=your-cloud
```

### Deployment Steps

```
Frontend (Vercel):
1. Connect GitHub repo to Vercel
2. Set environment variables in Vercel dashboard
3. Auto-deploys on every push to `main` branch
4. Preview deployments for pull requests

Backend (Heroku — Django):
1. Install Heroku CLI: npm install -g heroku
2. heroku login
3. heroku create your-app-name
4. Add buildpack: heroku buildpacks:set heroku/python
5. Add Heroku Postgres: heroku addons:create heroku-postgresql:mini
6. Set Config Vars: heroku config:set DJANGO_SECRET_KEY=xxx ...
7. Deploy: git push heroku main
8. Run migrations: heroku run python manage.py migrate
9. Create superuser: heroku run python manage.py createsuperuser
10. Access admin: https://your-app.herokuapp.com/admin/

Required Files for Heroku:
├── Procfile:          web: gunicorn config.wsgi --log-file -
├── runtime.txt:       python-3.12.x
├── requirements.txt:  All Python packages
└── .python-version:   3.12

Database (Supabase):
1. Create project on supabase.com
2. Run SQL migrations (schema above)
3. Configure RLS policies
4. Enable Phone Auth (OTP)
5. Set up Storage bucket for any Supabase-stored files

Note: You can use EITHER Supabase PostgreSQL OR Heroku Postgres as primary DB.
Recommendation: Use Supabase for DB + Auth + Realtime. 
Heroku Postgres as backup / if Supabase free tier limits are hit.

n8n:
1. Already self-hosted — configure workflows
2. Set webhook URLs in Heroku config vars
3. Configure MSG91 credentials in n8n
4. Test each workflow end-to-end
```

---

## 14. DEVELOPMENT SPRINT PLAN

### 6-Week Timeline (Solo Developer)

```
WEEK 1: Foundation
├── Day 1-2: Project setup
│   ├── Initialize Next.js project (frontend)
│   ├── Initialize Django project (backend)
│   │   └── django-admin startproject config .
│   │   └── Create apps: users, buses, bookings, payments, reviews
│   ├── Connect Supabase (create project, set up tables)
│   ├── Configure Cloudinary account
│   ├── Set up Git repo + branching strategy
│   ├── Set up Heroku app (heroku create)
│   └── Set up development environment (.env files)
│
├── Day 3-4: Authentication
│   ├── Phone OTP login (Supabase Auth or custom)
│   ├── DRF Token/JWT authentication middleware
│   ├── Role-based access control (customer, operator, admin)
│   ├── Login / Register pages (Next.js)
│   └── DRF permission classes (IsCustomer, IsOperator, IsAdmin)
│
├── Day 5-7: Database + Core API
│   ├── Define Django models (all tables)
│   ├── Run migrations (python manage.py migrate)
│   ├── Configure Django Admin (register all models)
│   ├── Build User DRF serializers + viewsets
│   ├── Build Bus DRF serializers + viewsets
│   └── Cloudinary upload integration
│
│ Deliverable: Users can register, login, and operators can add buses
│ 
├──────────────────────────────────────────────

WEEK 2: Operator Features
├── Day 1-2: Bus Management
│   ├── Add bus form (multi-step: details → photos → amenities → pricing)
│   ├── Photo upload to Cloudinary (drag-drop, reorder)
│   ├── Amenities selection (checkboxes)
│   ├── Pricing configuration
│   └── Edit bus details
│
├── Day 3-4: Availability Calendar
│   ├── Calendar component (monthly view)
│   ├── Block/unblock dates
│   ├── Visual indicators (green/red/orange)
│   └── API: Check availability for a date
│
├── Day 5-7: Document Upload
│   ├── Document upload form (RC, permit, insurance, etc.)
│   ├── Upload to Cloudinary (private/restricted)
│   ├── Document listing with status
│   └── Expiry date tracking
│
│ Deliverable: Operators can fully list buses with photos, calendar, and documents
│
├──────────────────────────────────────────────

WEEK 3: Customer Search & Browse
├── Day 1-3: Search Engine
│   ├── Search API with filters
│   │   ├── Location matching
│   │   ├── Date availability check
│   │   ├── Capacity filter
│   │   ├── Price range filter
│   │   ├── Bus type filter
│   │   ├── Sort: price, rating, popularity
│   │   └── Pagination
│   ├── Search results page (responsive cards)
│   ├── Filter sidebar / bottom sheet (mobile)
│   └── "No results" state with suggestions
│
├── Day 4-5: Bus Detail Page
│   ├── Photo gallery (swipe on mobile)
│   ├── Specifications display
│   ├── Amenities with icons
│   ├── Price breakdown
│   ├── Operator info section
│   ├── Reviews section
│   └── "Book Now" CTA
│
├── Day 6-7: Landing Page
│   ├── Hero section with search form
│   ├── How it works (3 steps)
│   ├── Featured buses
│   ├── Customer testimonials
│   ├── Operator CTA (list your bus)
│   └── SEO meta tags
│
│ Deliverable: Customers can search, browse, and view bus details
│
├──────────────────────────────────────────────

WEEK 4: Booking & Payments
├── Day 1-2: Booking Engine
│   ├── Booking creation API
│   │   ├── Availability re-check (prevent race conditions)
│   │   ├── Price calculation
│   │   ├── Commission calculation
│   │   ├── Booking number generation
│   │   └── Block date in availability
│   ├── Booking form (checkout page)
│   │   ├── Trip summary
│   │   ├── Payment mode selection
│   │   ├── Coupon code input
│   │   └── Special requests
│   └── Booking confirmation page
│
├── Day 3-4: Cashfree Integration
│   ├── Install cashfree-pg Python SDK
│   ├── Create Cashfree order (backend)
│   ├── Cashfree JS Drop-in component (frontend)
│   ├── Payment verification (webhook)
│   ├── Signature verification (security)
│   ├── Payment success/failure pages
│   └── Refund API integration
│
├── Day 5-7: Booking Management
│   ├── Customer: My bookings list + detail
│   ├── Operator: Incoming bookings list
│   ├── Operator: Accept/Reject booking
│   ├── Customer: Cancel booking
│   ├── Status transitions (pending → confirmed → completed)
│   └── WhatsApp contact button (for confirmed bookings)
│
│ Deliverable: Complete booking + payment flow works end-to-end
│
├──────────────────────────────────────────────

WEEK 5: Admin + Reviews + Notifications
├── Day 1-2: Admin Panel
│   ├── Django Admin customization (django-jazzmin theme)
│   ├── Custom admin actions (approve operator, send SMS)
│   ├── Admin dashboard widgets (stats overview)
│   ├── Operator verification workflow in admin
│   └── Coupon management (CRUD)
│
├── Day 3-4: Reviews & Ratings
│   ├── Review submission form (star ratings + text + photos)
│   ├── Review display on bus detail page
│   ├── Average rating calculation (trigger or computed)
│   ├── Review moderation (admin)
│   └── "Rate your trip" prompt (after completion)
│
├── Day 5-7: n8n Workflows
│   ├── Booking confirmation SMS (workflow 1)
│   ├── Operator response timeout (workflow 2)
│   ├── Daily calendar reminder (workflow 3)
│   ├── Review request post-trip (workflow 4)
│   ├── New operator notification to admin (workflow 6)
│   └── Test all workflows end-to-end
│
│ Deliverable: Admin can manage platform, reviews work, SMS notifications active
│
├──────────────────────────────────────────────

WEEK 6: Polish & Launch
├── Day 1-2: Hindi Translation
│   ├── Set up next-intl / i18n library
│   ├── Extract all strings to locale files
│   ├── Hindi translations for all UI
│   ├── Language toggle in header
│   └── Test RTL/Hindi rendering
│
├── Day 3-4: PWA + Responsive
│   ├── Configure next-pwa
│   ├── manifest.json + icons
│   ├── Offline fallback page
│   ├── Responsive testing (all screens, all breakpoints)
│   ├── Performance optimization (image lazy loading, code splitting)
│   └── "Add to Home Screen" prompt
│
├── Day 5: Testing
│   ├── End-to-end flow testing (search → book → pay → review)
│   ├── Payment testing (Cashfree sandbox → production)
│   ├── SMS delivery testing
│   ├── Edge cases (double booking, cancellation, refund)
│   ├── Cross-browser testing (Chrome, Samsung Internet, Firefox)
│   └── Beta testing with friends (10 users)
│
├── Day 6-7: Deploy & Launch
│   ├── Deploy backend to Heroku (git push heroku main)
│   ├── Run migrations on Heroku (heroku run python manage.py migrate)
│   ├── Create admin superuser on Heroku
│   ├── Deploy frontend to Vercel (production)
│   ├── Switch Cashfree to production mode
│   ├── Switch MSG91 to live mode
│   ├── Final smoke test on production
│   ├── Seed initial data (family buses via Django admin)
│   └── 🚀 LAUNCH!
│
│ Deliverable: Production-ready platform live with initial buses
```

---

## 15. TESTING STRATEGY

### Manual Testing Checklist (Friend Testers)

```
Customer Flow:
□ Can register with phone OTP
□ Can search buses by route and date
□ Can filter results
□ Can view bus details and photos
□ Can create a booking
□ Can pay via Cashfree (sandbox mode)
□ Can see booking confirmation
□ Can view booking history
□ Can cancel booking and receive refund
□ Can submit review after trip
□ Can switch language (Hindi ↔ English)
□ Can install PWA ("Add to Home Screen")
□ All pages responsive on mobile

Operator Flow:
□ Can register as operator
□ Can add bus with photos
□ Can set pricing and amenities
□ Can manage availability calendar
□ Can view incoming bookings
□ Can accept/reject booking
□ Can mark trip as completed
□ Can view earnings
□ Can upload documents

Admin Flow:
□ Can view dashboard stats
□ Can approve/reject operators
□ Can approve/reject buses
□ Can view all bookings
□ Can manage coupons
□ Can moderate reviews

Edge Cases:
□ Try booking already-booked date (should fail gracefully)
□ Try booking with expired payment (should timeout)
□ Operator rejects booking (customer gets refund)
□ Slow internet (loading states, error handling)
□ Empty states (no buses found, no bookings yet)
```

### Automated Tests (If Time Permits)
```
Backend (Django):
- API endpoint tests (Django TestCase + DRF APITestCase)
- Payment webhook verification test
- Booking conflict prevention test
- python manage.py test

Frontend:
- Component rendering tests (React Testing Library)
- Search filter logic tests
```

---

## 16. COST BREAKDOWN

### One-Time Costs
| Item | Cost | Notes |
|---|---|---|
| Domain | ₹0 | Already owned |
| Cloudinary setup | ₹0 | Free account |
| Supabase setup | ₹0 | Free project |
| Cashfree setup | ₹0 | No setup fee |
| Heroku setup | ₹0 | $320 free credits |
| n8n setup | ₹0 | Self-hosted |
| **Total One-Time** | **₹0** | |

### Monthly Recurring (First 6 Months)
| Item | Cost/Month | Free Tier Limits |
|---|---|---|
| Vercel (Frontend) | ₹0 | 100GB bandwidth, 1000 builds |
| Heroku (Django Backend) | ₹0 | $320 credits = Eco dyno $5/mo for 64 months |
| Supabase (Database) | ₹0 | 500MB DB, 1GB storage, 2GB bandwidth |
| Cloudinary (Images) | ₹0 | 25GB storage, 25GB bandwidth |
| MSG91 (SMS) | ~₹250/mo | ₹1,500 for 5000 SMS (onboard) |
| Azure AI (v2) | ₹0 | $100 credits cover 6+ months |
| Cashfree | 1.95% per txn | Deducted from revenue |
| **Total Monthly** | **~₹250** | |

### When Free Tiers Run Out (Estimated at ~1000 bookings)
| Item | Paid Cost/Month | When |
|---|---|---|
| Supabase Pro | $25 (~₹2,100) | After 500MB DB |
| Cloudinary | $99 (~₹8,300) | After 25GB images (unlikely in Year 1) |
| Vercel Pro | $20 (~₹1,700) | If traffic exceeds free tier |
| Heroku | Still covered | $320 credits last 5+ years at $5/mo |
| **Total Paid** | **~₹4,000 - ₹12,000/month** | **Only after revenue supports it** |

### Total First 6 Months Cost
```
SMS: ₹1,500 (one-time pack)
Everything else: ₹0 (credits/free tiers)

Total: ~₹1,500

Remaining from ₹5,000 budget: ₹3,500 → Use for first customer discounts
```

---

## 17. OPEN DECISIONS

### Decision 1: RESOLVED — Backend = Django + DRF ✅
```
Django chosen. Hosted on Heroku ($320 credits).
Benefits: Admin panel (free), DRF (fast API dev), ORM (auto migrations)
v2 Chat: Use Supabase Realtime (no Django Channels needed)
```

### Decision 2: App Name / Brand (NEEDS DECISION)
```
Options to consider:
- BusBook
- RideRaja
- BusWala
- SawariBook
- YatraaBus
- CharterKaro

ACTION: Decide before Week 1 (needed for domain, branding, PWA name)
```

### Decision 3: Supabase Auth vs Custom JWT
```
Supabase Auth Pros:
+ Phone OTP built-in (uses Twilio under the hood)
+ Session management automatic
+ Row-Level Security integration
+ Zero code for basic auth

Supabase Auth Cons:
- Free tier: 50K MAU (more than enough)
- SMS costs: Supabase charges for OTP SMS on free tier
  → Alternative: Use MSG91 for OTP and Supabase for session only

RECOMMENDATION: Use Supabase Auth for session management
but send OTP via MSG91 (cheaper) with custom verification flow
```

### Decision 4: Commission Collection for Cash Bookings
```
Options:
A. Operator security deposit (₹5,000 upfront, deduct commission)
B. Monthly invoice (trust-based, risky)
C. No cash bookings in MVP (100% online only)
D. Wallet system (operator maintains platform wallet balance)

RECOMMENDATION: Option A for MVP. 
Simple and protects platform revenue.
```

### Decision 5: RESOLVED — Payment Gateway = Cashfree ✅
```
Cashfree chosen. Already available.
Python SDK: pip install cashfree-pg
Transaction fee: 1.95% (cheaper than Razorpay's 2%)
Features: UPI, Cards, NetBanking, Payouts API for operators
```

### Decision 6: RESOLVED — Hosting = Heroku ✅
```
Heroku chosen. $320 credits available.
Eco dyno: $5/month = 64 months covered
No sleep issues (Eco dynos stay active)
One-command deploy: git push heroku main
Built-in PostgreSQL addon (backup DB option)
```

---

## APPENDIX

### Folder Structure (Django Backend)
```
/bus-booking-backend
├── manage.py
├── Procfile                     # web: gunicorn config.wsgi --log-file -
├── runtime.txt                  # python-3.12.x
├── requirements.txt             # All Python packages
├── .env                         # Local env vars (not committed)
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Common settings
│   │   ├── development.py       # Local dev settings
│   │   └── production.py        # Heroku production settings
│   ├── urls.py                  # Root URL configuration
│   └── wsgi.py                  # WSGI entry point (Heroku uses this)
├── apps/
│   ├── users/
│   │   ├── models.py            # User model (customer, operator, admin)
│   │   ├── views.py             # DRF ViewSets
│   │   ├── serializers.py       # DRF Serializers
│   │   ├── urls.py              # URL patterns
│   │   ├── admin.py             # Django Admin config
│   │   ├── permissions.py       # Custom DRF permissions
│   │   └── signals.py           # Post-save signals
│   ├── buses/
│   │   ├── models.py            # Bus, BusPhoto, BusAmenity, AvailabilityBlock
│   │   ├── views.py             # Search, CRUD viewsets
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py             # Bus admin with photo inline
│   │   └── filters.py           # django-filter search filters
│   ├── bookings/
│   │   ├── models.py            # Booking, Coupon, CouponUsage
│   │   ├── views.py             # Booking create, accept, reject, cancel
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py             # Booking admin with status actions
│   │   └── services.py          # Booking business logic
│   ├── payments/
│   │   ├── models.py            # Payment records
│   │   ├── views.py             # Cashfree order creation, webhook
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── cashfree.py          # Cashfree SDK wrapper
│   ├── reviews/
│   │   ├── models.py            # Review with ratings
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py             # Review moderation
│   ├── documents/
│   │   ├── models.py            # Operator documents
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py             # Document verification
│   └── notifications/
│       ├── models.py            # In-app notifications
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
├── utils/
│   ├── cloudinary_utils.py      # Cloudinary upload helpers
│   ├── n8n_triggers.py          # Trigger n8n webhooks
│   ├── pricing.py               # Price calculation logic
│   └── helpers.py               # Common helpers
└── static/                      # Django static files (for admin)

Key Python Packages (requirements.txt):
├── Django==5.1
├── djangorestframework==3.15
├── django-cors-headers           # CORS for Next.js frontend
├── django-filter                 # API filtering
├── django-jazzmin                # Modern admin theme
├── gunicorn                      # Production WSGI server (Heroku)
├── whitenoise                    # Static files on Heroku
├── dj-database-url               # Parse DATABASE_URL (Heroku)
├── python-decouple               # Env vars handling
├── cashfree-pg                   # Cashfree payment SDK
├── cloudinary                    # Image upload
├── supabase                      # Supabase Python client
├── requests                      # HTTP calls (n8n webhooks)
└── psycopg2-binary               # PostgreSQL adapter
```

### Folder Structure (Next.js Frontend)
```
/bus-booking-frontend
├── public/
│   ├── icons/                   # PWA icons
│   ├── manifest.json
│   └── sw.js                    # Service worker
├── src/
│   ├── app/
│   │   ├── (public)/            # Public routes group
│   │   │   ├── page.tsx         # Landing page
│   │   │   ├── search/page.tsx  # Search results
│   │   │   ├── bus/[id]/page.tsx # Bus detail
│   │   │   └── login/page.tsx   # Login
│   │   ├── (customer)/          # Customer routes group
│   │   │   ├── bookings/page.tsx
│   │   │   ├── bookings/[id]/page.tsx
│   │   │   ├── checkout/[id]/page.tsx
│   │   │   └── profile/page.tsx
│   │   ├── operator/            # Operator routes
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── buses/page.tsx
│   │   │   ├── buses/new/page.tsx
│   │   │   ├── buses/[id]/edit/page.tsx
│   │   │   ├── bookings/page.tsx
│   │   │   ├── earnings/page.tsx
│   │   │   └── documents/page.tsx
│   │   ├── admin/               # Admin routes
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── operators/page.tsx
│   │   │   ├── bookings/page.tsx
│   │   │   ├── reviews/page.tsx
│   │   │   └── coupons/page.tsx
│   │   ├── layout.tsx           # Root layout
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                  # Reusable UI (Button, Card, Modal, Input)
│   │   ├── search/              # Search bar, filters, results card
│   │   ├── booking/             # Booking form, summary, status
│   │   ├── bus/                 # Bus card, photo gallery, amenities
│   │   ├── operator/            # Dashboard widgets, calendar
│   │   ├── admin/               # Admin components
│   │   └── layout/              # Header, Footer, Sidebar, LanguageToggle
│   ├── lib/
│   │   ├── api.ts               # API client (axios/fetch wrapper)
│   │   ├── supabase.ts          # Supabase client
│   │   ├── auth.ts              # Auth helpers
│   │   └── utils.ts             # Utility functions
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useBooking.ts
│   │   └── useSearch.ts
│   ├── locales/
│   │   ├── en.json              # English translations
│   │   └── hi.json              # Hindi translations
│   └── types/
│       └── index.ts             # TypeScript interfaces
├── next.config.js
├── tailwind.config.js           # Using Tailwind CSS
├── package.json
└── .env.local
```

---

**END OF PRD v2.0 — Finalized**

**NEXT STEPS:**
1. Share this PRD with your friend for review
2. Finalize app name / brand identity
3. Set up accounts — Heroku, Supabase, Cashfree (sandbox), Cloudinary, MSG91
4. Start building (Week 1: Django project + Supabase DB + Next.js scaffold)
