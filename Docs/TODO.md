# Bus Booking Platform - Development Roadmap & Todo List

**Project:** Bus Booking Platform  
**Target Launch:** April 2026 (6-8 weeks)  
**Status:** Ready to Build  
**Last Updated:** February 12, 2026

---

## 📊 Project Overview

```
Phase 1: Backend Foundation (Week 1-2)     [BACKLOG]
Phase 2: Frontend Foundation (Week 1-2)    [BACKLOG]
Phase 3: Core Features (Week 3-4)          [BACKLOG]
Phase 4: Integration (Week 4-5)            [BACKLOG]
Phase 5: Testing & Optimization (Week 6)   [BACKLOG]
Phase 6: Deployment & Launch (Week 6-8)    [BACKLOG]
```

---

# 🔧 PHASE 1: BACKEND FOUNDATION

**Duration:** Week 1-2  
**Status:** [  ] Not Started

## Tasks

### P1.1: Django Project Setup & Configuration
- [x] Install Django dependencies from requirements.txt
- [x] Create Django admin user (superuser)
- [x] Configure environment variables (.env file)
- [x] Test database connection (PostgreSQL)
- [x] Run initial migrations
- [x] Verify development server runs (http://localhost:8000)
- [x] Confirm API documentation available at /api/docs

### P1.2: User Authentication System
- [x] Create CustomUser model with phone-based authentication
- [x] Implement user roles (customer, operator, admin)
- [x] Setup Supabase integration for OTP verification
- [x] Create serializers for user registration/login
- [x] Build authentication API endpoints
- [x] Test OTP flow (send & verify)
- [x] Create user profile endpoints (GET, PUT)

### P1.3: Bus Management Module
- [x] Create Bus model with all fields from PRD schema
- [x] Create BusPhoto, BusAmenity, AvailabilityBlock models
- [x] Build bus serializers (list, detail, operator views)
- [x] Create bus search API with filters
- [x] Implement availability checking logic
- [x] Create operator bus management endpoints
- [x] Test search with various filters (type, price, amenities)

### P1.4: Booking System
- [x] Create Booking model with full specification from PRD
- [x] Create Payment model for Cashfree integration
- [x] Create BookingHistory model for status tracking
- [x] Build booking creation logic with pricing calculation
- [x] Implement booking status workflow
- [x] Create payment initiation flow (Cashfree integration stub)
- [x] Test booking creation and validation

### P1.5: Reviews & Ratings
- [x] Create BusReview and OperatorReview models
- [x] Implement automatic rating calculation
- [x] Build review creation API
- [x] Create review listing API with pagination
- [x] Test review submission and retrieval

- [x] Implement review approval/flagging (admin)
### P1.6: Document Management
- [x] Create Document model for operator documents
- [x] Build document upload endpoint
- [x] Implement document verification workflow (admin)
- [x] Create document listing API
- [x] Test upload and verification flow

### P1.7: Admin Panel Customization
- [x] Install django-jazzmin for modern admin UI
- [x] Customize admin for Users app
- [x] Customize admin for Buses app
- [x] Customize admin for Bookings app
- [x] Customize admin for Reviews app
- [x] Customize admin for Documents app
- [x] Test admin panel (login, navigation, CRUD operations)

### P1.8: Testing & Documentation
- [x] Write unit tests for all models
- [x] Write API endpoint tests
- [x] Document all API endpoints
- [x] Create postman collection for manual testing
- [x] Test error handling and validation
- [x] Verify all database migrations work

---

## 🔗 Phase 1 - Copilot Prompt

For faster development, use this prompt with Copilot:

```
You are an expert Django developer. I'm building a Bus Booking Platform backend.

PHASE 1 - BACKEND FOUNDATION (Complete all following tasks):

DATABASE & MODELS:
1. Create all models exactly as specified in PRD (Section 4):
   - CustomUser with phone-based auth, roles (customer/operator/admin)
   - Bus with all fields (name, type, capacity, pricing, etc)
   - BusPhoto, BusAmenity, AvailabilityBlock (related to Bus)
   - Booking with full workflow support
   - Payment model for Cashfree
   - BookingHistory for tracking status changes
   - BusReview and OperatorReview
   - Document model for operator documents
   - OperatorNotification model

2. Use Django best practices:
   - Add proper indexes on frequently queried fields
   - Use UUIDs for all primary keys
   - Add timestamps (created_at, updated_at) to all models
   - Use DECIMAL for monetary fields
   - Implement cascade deletion where appropriate
   - Add helpful __str__ methods

API ENDPOINTS & SERIALIZERS:
1. Create serializers for all models
2. Implement REST API endpoints (use DRF ViewSets):
   - Users: register, login, profile, roles
   - Buses: list, search, detail, create (operator), update, delete
   - Bookings: create, list, detail, cancel, history
   - Reviews: create, list
   - Documents: upload, list, verify (admin)
   - Payments: initiate, verify

AUTHENTICATION:
1. Implement phone-based OTP authentication via Supabase
2. Create login/register endpoints
3. Add token-based authentication to all protected endpoints
4. Implement role-based access control (customer/operator/admin)

ADMIN PANEL:
1. Customize Django admin with django-jazzmin
2. Create readable list_display for each model
3. Add filters and search fields
4. Make sensitive fields read-only where needed

Expected deliverables:
✓ All models properly defined and migrated
✓ All API endpoints working
✓ Authentication system functional
✓ Admin panel customized and accessible
✓ Database properly indexed
✓ Error handling implemented

For each model, generate migration file automatically with:
python manage.py makemigrations
python manage.py migrate

Test everything thoroughly. If authentication doesn't work, debug Supabase configuration.
```

---

# 🎨 PHASE 2: FRONTEND FOUNDATION

**Duration:** Week 1-2  
**Status:** [  ] Not Started

## Tasks

### P2.1: Next.js Project Setup
- [ ] Install dependencies from package.json
- [ ] Setup TypeScript configuration
- [ ] Configure Tailwind CSS and PostCSS
- [ ] Test development server (http://localhost:3000)
- [ ] Verify hot reload working
- [ ] Setup environment variables (.env.local)

### P2.2: Core Layout & Navigation
- [ ] Create root layout with proper metadata
- [ ] Create page layout component
- [ ] Implement navigation header (with language toggle)
- [ ] Create footer component
- [ ] Implement mobile-responsive design
- [ ] Test layout on mobile, tablet, desktop
- [ ] Setup PWA manifest and icons

### P2.3: Authentication Pages
- [ ] Create login page with OTP input
  - [ ] Phone number input field
  - [ ] OTP send logic
  - [ ] OTP verification
  - [ ] Error handling and validation
- [ ] Create register page
  - [ ] Form for phone, email, name, role
  - [ ] Role selection (customer/operator)
  - [ ] Form validation
  - [ ] Success message
- [ ] Integrate Supabase Auth
- [ ] Test OTP flow end-to-end

### P2.4: State Management Setup
- [ ] Setup Zustand stores:
  - [ ] useAuthStore (user, isLoggedIn, setUser, logout)
  - [ ] useSearchStore (search filters)
  - [ ] useUIStore (language, sidebar state)
- [ ] Create protected route wrapper
- [ ] Implement persistent authentication
- [ ] Test state management

### P2.5: API Integration
- [ ] Create Axios API client with token injection
- [ ] Create API endpoints wrapper (API.ts)
- [ ] Implement error handling for API calls
- [ ] Setup API interceptors (auth, error handling)
- [ ] Test API client with backend endpoints
- [ ] Create loading states and error messages

### P2.6: Home Page
- [ ] Create landing page with hero section
- [ ] Add search bar (basic, will be expanded later)
- [ ] Create feature cards section
- [ ] Add how-it-works section
- [ ] Add testimonials section
- [ ] Make responsive (mobile-first)
- [ ] Test on all devices

### P2.7: Internationalization (i18n)
- [ ] Create translation objects for English & Hindi
- [ ] Setup language toggle in header
- [ ] Implement language persistence (localStorage)
- [ ] Translate all UI strings
- [ ] Test language switching

### P2.8: Testing & Polish
- [ ] Test responsive design on actual mobile device
- [ ] Verify PWA functionality (installable)
- [ ] Test performance (Lighthouse)
- [ ] Fix accessibility issues
- [ ] Test in different browsers (Chrome, Safari, Firefox)

---

## 🎨 Phase 2 - Copilot Prompt

```
You are an expert Next.js 14 developer. I'm building the frontend for Bus Booking Platform.

PHASE 2 - FRONTEND FOUNDATION (Complete all following tasks):

PROJECT SETUP:
1. Ensure all dependencies installed (npm install)
2. Setup TypeScript properly (tsconfig.json configured)
3. Configure Tailwind CSS with custom colors from tailwind.config.js
4. Verify Next.js app router working properly
5. Setup environment variables for Supabase and API

CORE COMPONENTS & PAGES:
1. Create reusable components:
   - Header (with language toggle, navigation, login/logout)
   - Footer (links, copyright)
   - LoadingSpinner
   - Modal components
   - Form input wrappers with validation
   - Card components

2. Create main pages:
   - / (landing page with hero, features, testimonials)
   - /login (OTP login flow)
   - /register (user registration form)
   - /dashboard (protected, shows quick actions)

AUTHENTICATION & SECURITY:
1. Integrate Supabase Auth for phone-based OTP:
   - Create signup with phone + metadata
   - Implement OTP verification
   - Store session in localStorage
   - Auto-redirect to login if unauthorized

2. Create protected route wrapper:
   - Redirect to login if not authenticated
   - Show loading state while checking auth
   - Persist user data in Zustand store

STATE MANAGEMENT:
1. Setup Zustand stores:
   - useAuthStore: { user, isLoggedIn, setUser, logout }
   - useSearchStore: { fromLocation, toLocation, pickupDate, passengers, setSearchParams }
   - useUIStore: { language, toggleLanguage, sidebarOpen, toggleSidebar }

2. Implement localStorage persistence for auth & language

API INTEGRATION:
1. Create Axios client (lib/api.ts):
   - Inject auth token to all requests
   - Handle 401 errors (redirect to login)
   - Global error handling

2. Create API endpoints wrapper with typed calls:
   - users: register, getProfile, updateProfile
   - buses: list, search, get, create, update
   - bookings: create, list, get, cancel
   - payments: initiate, confirm
   - reviews: create, list

INTERNATIONALIZATION:
1. Setup Hindi + English translations (lib/i18n.ts)
2. Create translation hook/function
3. Translate all UI text
4. Test language switching (localStorage persistence)

UI/UX STANDARDS:
1. Mobile-first responsive design
2. Consistent styling using Tailwind utilities
3. Proper spacing and typography
4. Touch-friendly buttons (min 44x44px)
5. Dark mode ready (optional)

TESTING & VALIDATION:
✓ All pages render without errors
✓ Authentication flow works (phone → OTP → token)
✓ API client properly sends requests with auth
✓ Language switching works and persists
✓ Responsive design works on mobile/tablet/desktop
✓ PWA manifest setup and app is installable

Focus on: Simple, clean UI • Fast performance • Mobile-first • Hindi/English support
```

---

# 🔑 PHASE 3: CORE FEATURES IMPLEMENTATION

**Duration:** Week 3-4  
**Status:** [  ] Not Started

## Tasks

### P3.1: Bus Search & Listing
- [ ] Create bus search page layout
- [ ] Implement location autocomplete
- [ ] Build date picker
- [ ] Create filter panel (type, AC, price, amenities)
- [ ] Implement advanced search endpoint call
- [ ] Display search results as cards
- [ ] Add sorting (price, rating, popularity)
- [ ] Implement pagination or infinite scroll
- [ ] Test search with various combinations

### P3.2: Bus Detail Page
- [ ] Create bus detail page layout
- [ ] Implement image gallery (swipeable on mobile)
- [ ] Display bus specifications
- [ ] Show amenities with icons
- [ ] Display pricing breakdown
- [ ] Show operator info with verification badge
- [ ] Display bus reviews (paginated)
- [ ] Add availability calendar
- [ ] Create "Book Now" button flow
- [ ] Test all interactions

### P3.3: Booking Workflow
- [ ] Create booking form/modal
- [ ] Implement passenger details collection
- [ ] Build trip type selector (one-way, round-trip)
- [ ] Create special requests textarea
- [ ] Calculate total price dynamically
- [ ] Implement coupon code input
- [ ] Show pricing breakdown
- [ ] Implement booking submission API call
- [ ] Handle validation errors
- [ ] Test complete booking flow

### P3.4: Customer Dashboard
- [ ] Create dashboard home page
- [ ] Display user profile info
- [ ] Show upcoming bookings (if any)
- [ ] Create quick action buttons
- [ ] Display booking history/stats
- [ ] Add profile edit link
- [ ] Test navigation to other sections

### P3.5: Booking Management (Customer)
- [ ] Create my bookings page
- [ ] Display booking list with status
- [ ] Create booking detail page
- [ ] Implement cancel booking functionality
- [ ] Show booking confirmation details
- [ ] Add print/download receipt functionality
- [ ] Create review submission flow
- [ ] Test all booking operations

### P3.6: Operator Registration Flow
- [ ] Create multi-step operator registration form
  - Step 1: Business info (name, type, GST, PAN)
  - Step 2: Bank details (account, IFSC, name)
  - Step 3: Document uploads
  - Step 4: Confirmation
- [ ] Implement form validation
- [ ] Create document upload with Cloudinary
- [ ] Display progress indicator
- [ ] Handle form submission
- [ ] Show success message
- [ ] Test complete flow

### P3.7: Operator Dashboard
- [ ] Create operator dashboard home
- [ ] Display stats (bookings, revenue, rating)
- [ ] Create quick action buttons
- [ ] Show upcoming bookings
- [ ] Create My Buses section
- [ ] Implement Add New Bus form
- [ ] Create bus edit functionality
- [ ] Implement availability calendar
- [ ] Test operator workflows

### P3.8: Payment Page
- [ ] Create payment page/modal
- [ ] Display payment options (UPI, card, net banking, pay driver)
- [ ] Integrate Cashfree payment gateway
- [ ] Handle payment response
- [ ] Implement payment verification
- [ ] Display payment status
- [ ] Handle errors and retries
- [ ] Test payment flow (use Cashfree sandbox)

### P3.9: Reviews & Ratings
- [ ] Create review submission form
- [ ] Implement star rating selector
- [ ] Add review text and photo upload
- [ ] Create reviews display component
- [ ] Implement review sorting/filtering
- [ ] Display overall rating calculation
- [ ] Test review functionality

### P3.10: Admin Dashboard (Basic)
- [ ] Create admin dashboard page
- [ ] Display platform stats
- [ ] Add user management quick links
- [ ] Create operator verification quick view
- [ ] Test admin navigation

---

## 🔑 Phase 3 - Copilot Prompt

```
You are an expert full-stack developer. I'm implementing core features for Bus Booking Platform.

PHASE 3 - CORE FEATURES (Complete all following tasks):

CUSTOMERS - SEARCH & BOOKING:
1. Bus Search Page (/search):
   - Location autocomplete input (call /api/locations/search)
   - Date picker (min: tomorrow, max: 90 days)
   - Passenger count select (7-50 people)
   - Trip type: one-way / round-trip / multi-day
   - [Search] button → POST /api/buses/search
   - Display results as grid of bus cards
   - Each card: photo, name, type, capacity, price, rating, amenities
   - Filters: Type, AC/Non-AC, Price slider, Rating, Amenities checkboxes
   - Sort: Price (low-high), Rating (high-low), Popularity
   - Pagination or infinite scroll

2. Bus Detail Page (/bus/[id]):
   - Image gallery (6-8 images, swipeable on mobile)
   - Bus specs: make, capacity, AC type, fuel, year, registration (partial)
   - Amenities list with icons
   - Pricing: ₹X/km × Y km + ₹Z base + tolls = Total
   - Distance calculator showing estimated km
   - Operator card: name, verified badge, member since, trips, rating
   - WhatsApp contact button (shows only after booking - don't show yet)
   - Reviews section: Latest 5 reviews, "See All" link
   - Cancellation policy
   - [Book This Bus] → Opens booking modal/page

3. Booking Creation (/checkout/[busId]):
   - Show booking summary (bus, route, date, passengers)
   - Collect: special requirements, passenger names (optional)
   - Payment mode selection:
     ✓ Pay Full Online (get insurance)
     ✓ Pay Advance ₹3000 (remaining to driver)
     ✓ Pay Driver (cash, ₹500 online fee)
   - Coupon code input with validation check
   - Dynamic price calculation with coupon
   - Terms & conditions checkbox
   - POST /api/bookings/create_booking → Get booking_id + redirect to payment

4. My Bookings Page (/my-bookings):
   - Tab navigation: All | Upcoming | Past | Cancelled
   - Booking list items showing:
     - Booking #, bus name, route, date, status
     - Amount paid, status chip
   - Click → Booking detail page
   - Cancel button (for pending & upcoming only)

5. Booking Detail (/bookings/[id]):
   - Full booking summary
   - Passenger count, special requests
   - Route details with distance
   - Price breakdown
   - Payment status + receipt
   - Status timeline (pending → confirmed → in-progress → completed)
   - Actions based on status:
     ✓ Cancel (if pending/upcoming)
     ✓ Download invoice
     ✓ Leave review (if completed)

OPERATORS - REGISTRATION & DASHBOARD:
1. Operator Registration (/become-operator):
   - Multi-step form with progress bar
   - STEP 1: Business details
     - Business name, type (individual/company)
     - GST number, PAN number
     - Address, city
   - STEP 2: Bank details
     - Account number, IFSC code, bank name
     - Account holder name
   - STEP 3: Documents (upload to Cloudinary)
     - Aadhar, PAN, Bank statement, RC book, Fitness, Permit, Insurance
   - STEP 4: Confirmation
     - Review all info
     - Agree to terms
   - POST to /api/users/operators/register_as_operator
   - Show success message "Awaiting verification"

2. Operator Dashboard (/operator/dashboard):
   - Stats cards: Bookings, Revenue (this month), Rating, Pending Requests
   - Quick actions: [Add Bus] [View Calendar] [Manage Docs] [View Earnings]
   - Upcoming trips: Show next 3-5 trips
   - Recent bookings: Show status + action buttons
   - Charts: Revenue trend, trips trend (optional for MVP)

3. My Buses (/operator/buses):
   - List of operator's buses with cards:
     - Photo thumbnail, name, registration, status badge
     - Rating, trip count, next booking date
     - [Edit] [Calendar] [Deactivate] buttons
   - [+ Add New Bus] button

4. Add/Edit Bus (/operator/buses/new, /operator/buses/[id]/edit):
   - Form fields:
     - Bus name, description
     - Type (mini, medium, luxury, tempo)
     - Capacity, sleeper capacity, notes
     - Registration, make/model, year, AC/fuel type
     - Price/km, base price, driver charge, night charge
   - Upload 6-8 bus photos (to Cloudinary)
   - Select amenities (checkboxes)
   - POST/PUT /api/operator/buses
   - Show success message

5. Availability Calendar (/operator/buses/[id]/calendar):
   - Monthly calendar view
   - Green: available, Red: booked, Orange: blocked/personal
   - Click date → Option to block/unblock
   - Block reason: maintenance, personal, external booking
   - Bulk action: Select date range → Block all
   - PUT /api/operator/buses/[id]/block-dates

PAYMENTS:
1. Payment Flow:
   - POST /api/payments/create-order → Get order_id from Cashfree
   - Redirect to Cashfree payment page
   - Handle payment response:
     ✓ Success → POST /api/payments/verify → Booking confirmed
     ✗ Failed → Show error, allow retry
   - Use Cashfree sandbox for testing (test credentials)

2. Payment Page (/checkout/[bookingId]):
   - Show order details + amount
   - Integrate Cashfree SDK
   - Handle success/failure redirects
   - Display payment status

REVIEWS:
1. Review Submission (/bookings/[id]/review):
   - Star rating (1-5 for overall)
   - Individual ratings: cleanliness, punctuality, driver, value
   - Review text textarea
   - Photo upload (optional)
   - POST /api/reviews/bus/create_review
   - Show success message

2. Review Display (on bus detail page):
   - Show avg rating prominently
   - List reviews sorted by newest/helpful
   - Show reviewer name, date, rating breakdown
   - Photos if available

ADMIN DASHBOARD (BASIC):
1. Admin Dashboard (/admin/dashboard):
   - Platform stats: Total users, operators, bookings, revenue
   - Quick verification links: Pending operators, pending documents
   - Recent bookings table with status filters
   - Navigation to admin section (rest in Django admin)

IMPORTANT TECHNICAL NOTES:
✓ All forms must validate on both client & server
✓ Show loading states during API calls
✓ Implement proper error messages
✓ Handle edge cases (no results, network errors, etc)
✓ Mobile-responsive throughout
✓ Test each flow end-to-end
✓ Use TypeScript for type safety
✓ Implement proper loading skeletons

Test all features thoroughly before moving to next phase!
```

---

# 🔗 PHASE 4: INTEGRATION & AUTOMATION

**Duration:** Week 4-5  
**Status:** [  ] Not Started

## Tasks

### P4.1: Cashfree Payment Integration
- [ ] Setup Cashfree merchant account
- [ ] Integrate Cashfree SDK on payment page
- [ ] Implement payment order creation
- [ ] Handle webhook callbacks from Cashfree
- [ ] Implement automatic booking confirmation on payment success
- [ ] Handle payment failures and refunds
- [ ] Test with Cashfree test cards
- [ ] Verify payout settlement flow

### P4.2: Cloudinary Integration
- [ ] Setup Cloudinary account and API credentials
- [ ] Create file upload wrapper component
- [ ] Implement image upload for bus photos
- [ ] Implement image upload for documents
- [ ] Setup image optimization (transformations)
- [ ] Handle upload errors and retries
- [ ] Test upload flow

### P4.3: n8n Automation Setup
- [ ] Setup n8n (self-hosted or cloud)
- [ ] Create SMS notification workflow (Booking Confirmed)
  - [ ] Trigger from backend webhook
  - [ ] Send SMS to customer via MSG91
  - [ ] Send SMS to operator via MSG91
  - [ ] Log notification in database
- [ ] Create SMS notification workflow (Booking Cancelled)
- [ ] Create Email notification workflow (optional)
- [ ] Test workflows with real data
- [ ] Setup webhook endpoint in backend

### P4.4: Email Integration
- [ ] Configure email service (SendGrid or AWS SES)
- [ ] Create email templates for notifications:
  - [ ] Booking confirmation email
  - [ ] Payment receipt email
  - [ ] Booking cancellation email
  - [ ] Review reminder email
- [ ] Implement email sending in backend
- [ ] Test email delivery

### P4.5: WhatsApp Integration (Optional)
- [ ] Setup WhatsApp Cloud API (if budget allows)
- [ ] Create WhatsApp templates
- [ ] Implement WhatsApp message sending
- [ ] Test WhatsApp flow
- [ ] Alternative: Direct WhatsApp link (current implementation)

### P4.6: Google Maps Integration (Optional for MVP)
- [ ] Setup Google Maps API
- [ ] Implement location autocomplete
- [ ] Implement distance calculator
- [ ] Implement route display on detail page
- [ ] Test location features

### P4.7: SMS Gateway Integration (MSG91)
- [ ] Setup MSG91 account
- [ ] Configure OTP templates
- [ ] Implement SMS sending for booking confirmations
- [ ] Test SMS delivery
- [ ] Setup fallback SMS provider

### P4.8: Monitoring & Logging
- [ ] Setup error tracking (Sentry)
- [ ] Implement request logging
- [ ] Setup uptime monitoring
- [ ] Create analytics events
- [ ] Test logging and monitoring

---

## 🔗 Phase 4 - Copilot Prompt

```
You are an expert integration engineer. I'm integrating payment & notification systems.

PHASE 4 - INTEGRATION & AUTOMATION (Complete all following tasks):

CASHFREE PAYMENT INTEGRATION:
1. Setup & Configuration:
   - Register Cashfree merchant account
   - Get APP_ID and SECRET_KEY from Cashfree Dashboard
   - Add to backend .env: CASHFREE_APP_ID, CASHFREE_SECRET_KEY
   - Use Cashfree API v2023-08-01

2. Backend Implementation (/api/payments/):
   - POST /api/payments/initiate-payment:
     ✓ Input: booking_id, payment_method
     ✓ Create Payment record in DB (status: pending)
     ✓ Call Cashfree API: POST /orders
     ✓ Response: order_id, payment_session_id, redirect_url
     ✓ Return payment_session_id to frontend
   
   - POST /api/payments/verify (webhook handler):
     ✓ Receive: order_id, payment_id, payment_status from Cashfree
     ✓ Verify signature from Cashfree
     ✓ Update Payment table: status='completed'
     ✓ Update Booking: status='confirmed', payment_status='completed'
     ✓ Trigger n8n webhook: booking_confirmed
     ✓ Return success response

3. Frontend Implementation:
   - On payment page, load Cashfree Modal with payment_session_id
   - Handle payment success → redirect to /bookings/[id]?success=true
   - Handle payment failure → show error, allow retry
   - Display payment status in booking details

4. Testing:
   - Use Cashfree test AppID/SecretKey
   - Test with Cashfree test payment methods
   - Verify webhook handling works
   - Test refund flow (if cancellation requested)

CLOUDINARY IMAGE UPLOAD:
1. Setup & Configuration:
   - Get Cloud Name, API Key, API Secret from Cloudinary
   - Add to .env: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
   - Setup unsigned uploads (optional, for faster client uploads)

2. Backend Implementation:
   - POST /api/operator/buses/[id]/photos:
     ✓ Receive: image file, photo_type
     ✓ Upload to Cloudinary (secure URL with transformations)
     ✓ Save photo_url to BusPhoto table
     ✓ Return photo URL
   
   - Implement image transformations:
     ✓ Auto quality optimization (q_auto)
     ✓ Responsive sizes (w_500, w_300 for thumbnails)
     ✓ Format conversion (f_auto)

3. Frontend Implementation:
   - Create <ImageUpload /> component:
     ✓ File input with image preview
     ✓ Show upload progress
     ✓ Handle errors gracefully
     ✓ Multiple file upload support
   - Display uploaded images in gallery
   - Allow delete/reorder operations

4. Document Upload:
   - Similar flow for operator documents
   - Store as private Cloudinary URL
   - Include document_type, expiry_date

N8N AUTOMATION WORKFLOWS:
1. Setup n8n (cloud.n8n.io or self-hosted):
   - Create webhook trigger: /n8n/booking-confirmed
   - Create webhook trigger: /n8n/booking-cancelled
   - Authentication: Simple key-based

2. Workflow 1: Booking Confirmed SMS
   - Trigger: POST /n8n/booking-confirmed
   - Input: { booking_id, customer_phone, customer_name, operator_phone, 
              bus_name, pickup_date, pickup_time, route, amount, pax }
   - Actions:
     ✓ MSG91 Send SMS to Customer:
       "Hi {name}, your bus booking #{booking_id} is confirmed!
        Bus: {bus_name}
        Route: {route}
        Date: {pickup_date} {pickup_time}
        Passengers: {pax}
        Amount: ₹{amount}
        Support: +919829012345"

     ✓ MSG91 Send SMS to Operator:
       "New booking! #{booking_id}
        Date: {pickup_date} {pickup_time}
        Route: {route}
        Passengers: {pax}
        Payout: ₹{payout}
        Accept in app within 1 hour."

     ✓ Supabase Insert: New notification record

3. Workflow 2: Booking Cancelled SMS
   - Similar to above, but for cancellation
   - Send refund amount to customer

4. Backend Integration:
   - After booking confirmed, POST to:
     curl -X POST https://n8n.your-domain.com/webhook/booking-confirmed \\
       -H "Content-Type: application/json" \\
       -d '{...payload...}'

SMS GATEWAY SETUP (MSG91):
1. Account Setup:
   - Register on MSG91.com
   - Verify phone number
   - Get API Key from dashboard
   - Add to .env: MSG91_API_KEY

2. SMS Templates (Create in MSG91):
   - OTP_TEMPLATE: "Your OTP is #OTP#"
   - BOOKING_CONFIRM: "[Bus Booking] Your booking is confirmed..."
   - BOOKING_CANCEL: "[Bus Booking] Your booking has been cancelled..."

3. SMS Sending (via n8n):
   - n8n MSG91 node: auth with API key
   - Send to customer & operator phone numbers
   - Handle delivery failures

EMAIL INTEGRATION (OPTIONAL):
1. Setup SendGrid:
   - Create account and get API key
   - Create email templates in SendGrid
   - Add API_KEY to .env

2. Email Templates:
   - Booking confirmation with receipt
   - Payment receipt
   - Cancellation notice with refund info

3. Backend Implementation:
   - Send email via SendGrid API on booking confirmation
   - Include attachment: invoice PDF (optional)

MONITORING & ERROR TRACKING:
1. Sentry Setup:
   - Create Sentry account
   - Add Sentry SDK to backend and frontend
   - Configure environment-based reporting
   - Test error capture

2. Logging:
   - Log all payment transactions
   - Log all SMS/email sends
   - Log API errors with full context
   - Setup log rotation

3. Health Checks:
   - Create /health endpoint for uptime monitoring
   - Monitor database connectivity
   - Monitor payment gateway connectivity

TESTING:
✓ Test complete booking → payment → confirmation flow
✓ Verify SMS received by both parties
✓ Test email delivery
✓ Test error scenarios (payment failed, SMS failed)
✓ Verify webhook signatures are validated
✓ Test image upload with various file types
✓ Test for security issues (file validation, CSRF, etc)

Make sure all integrations use proper error handling and retry logic!
```

---

# ✅ PHASE 5: TESTING & OPTIMIZATION

**Duration:** Week 6  
**Status:** [  ] Not Started

## Tasks

### P5.1: Unit Testing
- [ ] Write tests for all Django models
- [ ] Write tests for all serializers
- [ ] Write tests for business logic (pricing, availability)
- [ ] Write tests for authentication
- [ ] Achieve 80%+ code coverage for critical paths
- [ ] Run tests and fix failures

### P5.2: Integration Testing
- [ ] Test complete booking flow (end-to-end)
- [ ] Test payment flow with Cashfree sandbox
- [ ] Test operator registration flow
- [ ] Test search and filtering
- [ ] Test notification flows
- [ ] Test review submission and approval

### P5.3: API Testing
- [ ] Create Postman collection with all endpoints
- [ ] Test all request/response formats
- [ ] Test error handling and validation
- [ ] Test authentication and authorization
- [ ] Test rate limiting (if implemented)
- [ ] Test pagination and filtering

### P5.4: Frontend Testing
- [ ] Test all UI components
- [ ] Test form validation
- [ ] Test API error handling
- [ ] Test responsive design on actual devices
- [ ] Test accessibility (keyboard navigation, screen readers)
- [ ] Test with slow network (throttle in DevTools)
- [ ] Test browser compatibility

### P5.5: Performance Optimization
- [ ] Optimize database queries (N+1 problems)
- [ ] Add database indexes where needed
- [ ] Optimize images (Cloudinary compression)
- [ ] Implement caching (Redis if needed)
- [ ] Optimize frontend bundle size
- [ ] Implement lazy loading for images
- [ ] Test Core Web Vitals (LCP, FID, CLS)

### P5.6: Security Audit
- [ ] Check SQL injection vulnerabilities
- [ ] Check XSS vulnerabilities
- [ ] Check CSRF protection
- [ ] Verify authentication token security
- [ ] Check sensitive data handling (phone, payment info)
- [ ] Verify API authorization on all endpoints
- [ ] Check rate limiting on public endpoints
- [ ] Verify HTTPS usage everywhere

### P5.7: Load Testing
- [ ] Test with simulated concurrent users (100+ simultaneous)
- [ ] Monitor response times under load
- [ ] Check for memory leaks
- [ ] Test database connection pooling
- [ ] Monitor server resource usage

### P5.8: User Acceptance Testing (UAT)
- [ ] Create test scenarios for each user role
- [ ] Document expected vs actual behavior
- [ ] Test on production-like environment
- [ ] Get feedback from stakeholders
- [ ] Fix any discovered issues

---

## ✅ Phase 5 - Copilot Prompt

```
You are a QA engineer & performance specialist. I'm testing & optimizing Bus Booking Platform.

PHASE 5 - TESTING & OPTIMIZATION (Complete all following tasks):

UNIT TESTS (Django Backend):
1. Model Tests (apps/*/test_models.py):
   - Test CustomUser creation, validation
   - Test Bus model with various data
   - Test Booking calculations (pricing, distance, etc)
   - Test Payment model status transitions
   - Test Review rating calculations
   - Test Document verification workflow
   - Use pytest or Django TestCase
   - Achieve 80%+ code coverage for critical models

2. Serializer Tests (apps/*/test_serializers.py):
   - Test field validation (required, unique, etc)
   - Test nested serializers
   - Test custom validation methods
   - Test error messages are helpful

3. View/API Tests (apps/*/test_views.py):
   - Test authenticated vs unauthenticated access
   - Test permission checks (customer can't see others' bookings)
   - Test request/response formats
   - Test error responses (400, 404, 403)
   - Test pagination works
   - Test filtering/search works

4. Business Logic Tests (apps/*/test_logic.py):
   - Test booking confirmation flow
   - Test payment verification
   - Test availability checking
   - Test pricing calculations
   - Test cancellation policy logic

INTEGRATION TESTS:
1. End-to-End Flows:
   - Customer registration → Login → Search → Book → Pay → Review
   - Operator registration → Verify docs → Add bus → Receive booking → Accept → Complete
   - Admin workflow: Verify operator → Verify documents → Monitor bookings

2. Payment Flow Test:
   - Create booking → Initiate payment → Verify with Cashfree → Update status
   - Test with Cashfree test card (4111 1111 1111 1111)
   - Test payment failure scenario
   - Test refund flow

3. Notification Flow Test:
   - Booking confirmation → n8n webhook → SMS sent
   - Verify SMS content is correct
   - Verify both customer & operator got SMS
   - Test operator rejection → SMS sent

4. Database Flow Test:
   - Test cascading deletes
   - Test transaction rolled back on error
   - Test data consistency after failure

API TESTING (Postman/Collection):
1. Create comprehensive Postman collection:
   - Organize by feature (users, buses, bookings, etc)
   - Include test data/fixtures
   - Use pre-request scripts for auth token
   - Use tests for response validation

2. Test Scenarios:
   - Happy path (successful operations)
   - Error cases (validation, not found, unauthorized)
   - Edge cases (boundary values, special characters)
   - Rate limiting (if implemented)

3. Automated Tests:
   - Run collection with Newman CLI
   - Generate HTML report
   - Integrate with CI/CD

FRONTEND TESTING:
1. Component Testing:
   - Test form validation works
   - Test error messages display
   - Test loading states
   - Test API error handling
   - Test form submission

2. Page Testing:
   - Test authentication redirects
   - Test page loads correct data
   - Test navigation works
   - Test responsive design (320px, 768px, 1024px breakpoints)
   - Test on actual mobile device!

3. Accessibility Testing:
   - Test keyboard navigation (Tab key)
   - Test minimum contrast ratios
   - Test form labels are associated
   - Test alt text on images
   - Use axe-core or WAVE browser extension

4. Browser Compatibility:
   - Chrome (latest)
   - Firefox (latest)
   - Safari (latest)
   - Edge (latest)
   - Test on actual devices!

PERFORMANCE OPTIMIZATION:
1. Backend Optimization:
   - Identify N+1 query problems:
     ✗ Bad: for bus in buses: operator = bus.operator  (N queries)
     ✓ Good: buses.select_related('operator')
   - Add missing database indexes
   - Use .only() or .defer() for large models
   - Implement query caching with Redis (optional)
   - Profile code with django-silk or locust

2. Frontend Optimization:
   - Analyze bundle size: npm run build → Check .next/static
   - Remove unused dependencies
   - Implement image lazy loading <Image />
   - Optimize images with Cloudinary transformations
   - Implement code splitting for large pages
   - Test with Chrome DevTools (Lighthouse)
   - Target scores: Lighthouse 90+

3. Database Optimization:
   - Check query count in Django Debug Toolbar
   - Add indexes on frequently filtered fields
   - Archive old data if necessary
   - Configure connection pooling in Heroku PostgreSQL

4. Monitoring & Metrics:
   - Monitor API response times (target: <200ms)
   - Monitor database query times (target: <100ms)
   - Monitor frontend page load time (target: <2s)
   - Monitor error rate (target: <0.1%)

SECURITY AUDIT:
1. Input Validation:
   - Test SQL injection (try: ' OR '1'='1)
   - Test XSS attacks (try: <script>alert('xss')</script>)
   - Test file upload attacks (upload .exe, .php)
   - Verify all inputs are validated/sanitized

2. Authentication & Authorization:
   - Verify tokens expire properly
   - Verify customers can't see others' data
   - Verify operators can't edit other buses
   - Verify only admins can verify documents
   - Test with invalid/expired/forged tokens

3. Data Security:
   - Verify phone numbers are partially hidden
   - Verify payment info isn't logged
   - Verify sensitive documents are private
   - Test HTTPS only (no HTTP)

4. API Security:
   - Test rate limiting prevents brute force
   - Test CORS headers are correct
   - Verify CSRF tokens are validated
   - Test for exposed sensitive info in error messages

LOAD & STRESS TESTING (Optional for MVP):
1. Setup load testing with Apache JMeter or Locust
2. Simulate 100+ concurrent users
3. Monitor response times and error rates
4. Check for memory leaks
5. Identify breaking point

USER ACCEPTANCE TESTING (UAT):
1. Create test scenarios:
   - Customer: Find bus → Book → Pay → Review
   - Operator: Register → Upload docs → Add bus → Accept booking
   - Admin: Verify operator → View dashboard → Moderate review

2. Define acceptance criteria:
   - All features work as specified in PRD
   - No critical bugs
   - Performance acceptable (pages load <2s)
   - Mobile responsive
   - SMS notifications delivered

3. Document testing results
4. Get sign-off from stakeholders

TESTING CHECKLIST:
□ All unit tests pass
□ All integration tests pass
□ All API endpoints tested
□ Frontend pages tested on mobile
□ Payment flow tested (test cards)
□ SMS notifications verified
□ Security audit passed
□ Load testing successful
□ User acceptance testing complete
□ Code coverage >80% for critical paths
□ Lighthouse score >90
□ Zero high/critical security issues
□ Error rate <0.1%
□ API response time <200ms
□ Page load time <2s

Run tests often during development!
```

---

# 🚀 PHASE 6: DEPLOYMENT & LAUNCH

**Duration:** Week 6-8  
**Status:** [  ] Not Started

## Tasks

### P6.1: Backend Deployment (Heroku)
- [ ] Create Heroku app for Django backend
- [ ] Configure environment variables on Heroku
- [ ] Setup PostgreSQL database on Heroku
- [ ] Configure Django settings for production
- [ ] Setup SSL/HTTPS
- [ ] Run migrations on production database
- [ ] Create production superuser
- [ ] Test API endpoints on production
- [ ] Setup error monitoring (Sentry)
- [ ] Setup logging and monitoring
- [ ] Configure auto-scaling if needed

### P6.2: Frontend Deployment (Vercel)
- [ ] Create Vercel account
- [ ] Connect GitHub repository
- [ ] Configure environment variables on Vercel
- [ ] Setup custom domain (if available)
- [ ] Configure SSL/HTTPS
- [ ] Setup automatic deployments on git push
- [ ] Test frontend on production
- [ ] Configure analytics (Google Analytics)
- [ ] Setup error monitoring (Sentry)

### P6.3: Database Setup
- [ ] Migrate to production database (Heroku PostgreSQL or Supabase)
- [ ] Setup automated backups
- [ ] Configure connection pooling
- [ ] Monitor database performance
- [ ] Setup replication (if needed)

### P6.4: DNS & Domain Configuration
- [ ] Register domain (if not done)
- [ ] Configure DNS records
- [ ] Setup SSL certificates (auto via Vercel/Heroku)
- [ ] Test domain access

### P6.5: Third-Party Integrations (Production)
- [ ] Setup production Cashfree merchant account
- [ ] Setup production Cloudinary account
- [ ] Setup production MSG91 account
- [ ] Setup production n8n (or use n8n.io)
- [ ] Configure all API keys on deployed apps

### P6.6: Monitoring & Alerting
- [ ] Setup Sentry for error tracking
- [ ] Setup uptime monitoring
- [ ] Configure email alerts for critical errors
- [ ] Setup performance monitoring
- [ ] Create dashboard for key metrics

### P6.7: Documentation
- [ ] Write deployment guide
- [ ] Document configuration steps
- [ ] Write troubleshooting guide
- [ ] Document API documentation
- [ ] Create user guides (customer, operator, admin)

### P6.8: Launch Preparation
- [ ] Create launch checklist
- [ ] Setup support email/chat
- [ ] Create FAQ section
- [ ] Prepare marketing materials
- [ ] Setup analytics and tracking
- [ ] Train support team
- [ ] Plan soft launch (beta) period

### P6.9: Soft Launch (Beta)
- [ ] Deploy to production with limited access
- [ ] Test with real users (friends, family)
- [ ] Gather feedback
- [ ] Fix critical issues
- [ ] Monitor for bugs

### P6.10: Official Launch
- [ ] Deploy to production (full access)
- [ ] Announce launch
- [ ] Monitor 24/7 for issues
- [ ] Support users
- [ ] Track key metrics (DAU, bookings, revenue)

---

## 🚀 Phase 6 - Copilot Prompt

```
You are a DevOps engineer. I'm deploying Bus Booking Platform to production.

PHASE 6 - DEPLOYMENT & LAUNCH (Complete all following tasks):

BACKEND DEPLOYMENT TO HEROKU:
1. Heroku Setup:
   - Install Heroku CLI
   - heroku login
   - heroku create bus-booking-api (or custom name)
   - heroku git:remote -a bus-booking-api

2. Configure Environment Variables:
   - heroku config:set DEBUG=False
   - heroku config:set DJANGO_SECRET_KEY=<generate-random-secret>
   - heroku config:set ALLOWED_HOSTS=bus-booking-api.herokuapp.com,yourdomain.com
   - heroku config:set DATABASE_URL=<auto-set when adding PostgreSQL>
   - heroku config:set SUPABASE_URL=<your-url>
   - heroku config:set SUPABASE_KEY=<your-key>
   - heroku config:set CLOUDINARY_CLOUD_NAME=<your-name>
   - heroku config:set CLOUDINARY_API_KEY=<your-key>
   - heroku config:set CLOUDINARY_API_SECRET=<your-secret>
   - heroku config:set CASHFREE_APP_ID=<your-id>
   - heroku config:set CASHFREE_SECRET_KEY=<your-key>
   - heroku config:set SECURE_SSL_REDIRECT=True
   - heroku config:set SESSION_COOKIE_SECURE=True

3. PostgreSQL Database:
   - heroku addons:create heroku-postgresql:mini
   - Wait for database to be ready
   - heroku run python manage.py migrate
   - heroku run python manage.py createsuperuser
   - Verify database connection works

4. Static Files:
   - python manage.py collectstatic --noinput
   - Verify whitenoise is configured in settings.py
   - Files auto-served at /static/

5. Deploy:
   - git push heroku main
   - heroku logs --tail (watch deployment)
   - Once deployed: curl https://bus-booking-api.herokuapp.com/health
   - Should return 200 OK

6. Verify Production:
   - Test API: curl https://bus-booking-api.herokuapp.com/api/v1/buses
   - Test admin: https://bus-booking-api.herokuapp.com/admin
   - Check Heroku dashboard for dyno status

FRONTEND DEPLOYMENT TO VERCEL:
1. Vercel Setup:
   - Go to vercel.com
   - Sign up / login
   - Create new project from GitHub repo
   - Select "Next.js" project type
   - Vercel auto-detects next.config.js

2. Configure Environment Variables:
   - In Vercel Dashboard → Settings → Environment Variables
   - NEXT_PUBLIC_BACKEND_API=https://bus-booking-api.herokuapp.com
   - NEXT_PUBLIC_SUPABASE_URL=<your-url>
   - NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-key>
   - Make sure NEXT_PUBLIC_* vars start with NEXT_PUBLIC_

3. Deploy:
   - Every git push to main auto-deploys
   - Vercel shows build progress
   - Once deployed, visit provided URL
   - Should show home page without errors

4. Custom Domain (Optional):
   - Buy domain (Namecheap, GoDaddy, etc)
   - In Vercel Settings → Domains
   - Add your domain, follow CNAME setup
   - Setup SSL (auto via Vercel)

5. Verify Production:
   - Test homepage loads
   - Test login page loads
   - Test search button works (calls backend API)
   - Check in Chrome DevTools Network tab

DATABASE & BACKUPS:
1. Heroku PostgreSQL (Mini plan):
   - Auto-managed by Heroku
   - Manual backups: heroku pg:backups:capture -a bus-booking-api
   - Restore backup: heroku pg:backups:restore

2. Supabase Backups:
   - Auto bi-hourly snapshots (7-day retention)
   - Enable point-in-time recovery in settings
   - Test restore process in staging

3. Monitoring:
   - heroku addons (shows database status)
   - heroku ps (shows dyno status)
   - Heroku Dataclips for advanced queries

THIRD-PARTY INTEGRATIONS (PRODUCTION):
1. Cashfree:
   - Get production APP_ID & SECRET_KEY from dashboard
   - Update CASHFREE_APP_ID and CASHFREE_SECRET_KEY on Heroku
   - Update API endpoint: https://api.cashfree.com/pg/orders/
   - Test payment with real card (small amount)

2. Cloudinary:
   - Use production cloud name
   - Setup security: Dashboard → Security → Restricted media types
   - Enable signed uploads for sensitive images

3. MSG91 & n8n:
   - Setup production MSG91 account
   - Configure n8n with production credentials
   - Test SMS sending

4. Supabase:
   - Use production project  credentials
   - Enable RLS on all tables
   - Setup Row Level Security policies
   - Enable phone auth, disable email if not needed

5. Sentry (Error Tracking):
   - Create Sentry.io account
   - Create project for Django + Next.js
   - Get DSN for both
   - Add to Heroku config: SENTRY_DSN=...
   - Frontend: Add Sentry.init() in next.config.js or _app.tsx
   - Test by triggering error

MONITORING & ALERTING:
1. Sentry Setup:
   - Configure in both Django & Next.js
   - Setup alerts: Email on critical errors
   - Create Sentry dashboard for overview

2. Uptime Monitoring:
   - Setup Uptime Robot or similar
   - Monitor /health endpoint
   - Alert if down >5 minutes

3. Performance Monitoring:
   - Enable Heroku Metrics
   - Monitor in Heroku Dashboard
   - Alert on high memory/CPU usage

4. Database Monitoring:
   - Check Heroku Dataclips for slow queries
   - Monitor connection count
   - Alert if connections >90 max

GRADUAL ROLLOUT:
1. Soft Launch (Optional):
   - Deploy to production with limited access
   - Test with small group of real users
   - Monitor for critical issues
   - Fix bugs before full launch

2. Full Launch:
   - Open to all users
   - Monitor heavily first 24-48 hours
   - Have support team ready

LAUNCH CHECKLIST:
□ All environment variables configured
□ Database migrations run successfully
□ Superuser created
□ API endpoints accessible and working
□ Frontend loads without errors
□ Authentication flow works (SMS/OTP)
□ Search functionality working
□ Payment flow tested with test card
□ SMS notifications working
□ Admin panel accessible
□ Error tracking (Sentry) working
□ Custom domain pointing to app
□ SSL/HTTPS enabled everywhere
□ Backups configured and tested
□ Monitoring alerts configured
□ Support team trained
□ FAQ prepared
□ Social media posts scheduled

POST-LAUNCH MONITORING:
- Monitor error rates (target: <0.1%)
- Monitor API response times (target: <200ms)
- Monitor page load times (target: <2s)
- Track daily active users
- Track booking conversion rate
- Monitor customer support tickets
- Daily review of Sentry errors
- Weekly database backups verified
- Monthly cost review

Be ready to handle issues 24/7 for first week!
```

---

# 📊 Development Progress Tracker

## Completed Tasks

| Phase | Task | Status | Notes |
|-------|------|--------|-------|
| - | Project Setup | ✅ | File structure created |
| - | Documentation | ✅ | CONTEXT, PRD, SETUP done |

## Current Phase

**Phase:** [SELECT PHASE]  
**Current Task:** [CURRENT TASK]  
**Blockers:** None  
**Progress:** 0%

## Next Steps

1. Choose which phase to start with
2. Use the Copilot prompt provided for that phase
3. Check off tasks as completed
4. Move to next phase when complete

---

# 🎯 Quick Reference

## Running the App

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Access
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Admin: http://localhost:8000/admin
- API Docs: http://localhost:8000/api/docs
```

## Key Files

**Backend:**
- `backend/bus_booking/settings.py` - Configuration
- `backend/apps/users/models.py` - User model
- `backend/apps/buses/models.py` - Bus model
- `backend/apps/bookings/models.py` - Booking model

**Frontend:**
- `frontend/lib/api.ts` - API client
- `frontend/lib/store.ts` - State management
- `frontend/app/page.tsx` - Home page

## Deployment

- **Backend:** Heroku ($320 free credits)
- **Frontend:** Vercel (free)
- **Database:** Supabase PostgreSQL (free tier)
- **Images:** Cloudinary (free: 25GB)

---

# 📝 Notes

- Total MVP development time: 6-8 weeks
- Solo developer (you!)
- All cloud services have free tiers
- Focus on core features first
- Launch with minimum viable features
- Plan v2 for advanced features (chat, tracking, etc)

---

**Created:** February 12, 2026  
**Last Updated:** February 12, 2026  
**Status:** Ready to Build  
**Developer:** You! 🚀
