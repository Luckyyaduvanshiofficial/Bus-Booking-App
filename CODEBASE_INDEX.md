# 🗂️ CODEBASE INDEX - Bus Booking Platform

**Last Updated:** February 14, 2026  
**Purpose:** Comprehensive navigation index for the entire codebase  
**Use:** Quick reference for finding files, functions, models, endpoints

---

## 📁 PROJECT STRUCTURE

```
Bus Booking app/
├── backend/                    # Django REST API
│   ├── bus_booking/           # Project settings
│   ├── apps/                  # Django apps
│   │   ├── users/            # User management
│   │   ├── buses/            # Bus inventory
│   │   ├── bookings/         # Booking system
│   │   ├── reviews/          # Review system
│   │   └── common/           # Shared utilities
│   └── scripts/              # Utility scripts
├── frontend/                  # Next.js application
├── Docs/                      # Documentation
└── tmp/                       # Temporary files
```

---

## 🔧 BACKEND CONFIGURATION

### Core Files
| File | Path | Purpose |
|------|------|---------|
| **Settings** | `backend/bus_booking/settings.py` | Django configuration, DB, security |
| **URLs** | `backend/bus_booking/urls.py` | Root URL routing |
| **WSGI** | `backend/bus_booking/wsgi.py` | Production server entry |
| **Celery** | `backend/bus_booking/celery.py` | Async task configuration |
| **Requirements** | `backend/requirements.txt` | Python dependencies |
| **Procfile** | `backend/Procfile` | Heroku deployment config |

### Environment Variables
| Variable | Purpose | Location |
|----------|---------|----------|
| `DJANGO_SECRET_KEY` | Django security key | `.env` |
| `DB_NAME, DB_USER, DB_PASSWORD` | PostgreSQL connection | `.env` |
| `SUPABASE_URL, SUPABASE_KEY` | Supabase config | `.env` |
| `CLOUDINARY_*` | Image storage | `.env` |
| `CASHFREE_*` | Payment gateway | `.env` |
| `BREVO_API_KEY` | Email/WhatsApp | `.env` |
| `N8N_WEBHOOK_URL` | Notification webhook | `.env` |
| `CELERY_BROKER_URL` | Redis for tasks | `.env` |

---

## 📦 APP: USERS (`apps.users`)

### Models (`apps/users/models.py`)
| Model | Fields | Purpose |
|-------|--------|---------|
| **CustomUser** | id (UUID), phone, email, role, is_verified, city, language | User authentication & profiles |
| **Document** | id (UUID), user, document_type, number, file_url, expiry_date, verification_status | Operator document verification |
| **Notification** | id (UUID), user, title, message, notification_type, is_read | In-app notifications |

#### CustomUser Key Fields
- `role`: customer / operator / admin
- `is_verified`: Email/phone verified
- `verification_status`: pending / verified / rejected (for operators)
- `subscription_tier`: free / pro / enterprise
- `business_type`: individual / company
- `rating_avg`: Operator rating (0-5)
- `bank_account_encrypted`: Encrypted bank details

### Services (`apps/users/services.py`)
| Service | Methods | Purpose |
|---------|---------|---------|
| **AuthService** | `send_otp()`, `verify_otp()`, `register_user()` | Phone-based authentication |
| **OperatorService** | `create_operator()`, `update_operator()`, `approve_operator()` | Operator management |
| **DocumentService** | `upload_document()`, `verify_document()`, `reject_document()` | Document verification |
| **UserService** | `get_user_profile()`, `update_profile()`, `verify_user()` | User profile management |

### Views (`apps/users/views.py`)
| ViewSet/Endpoint | Methods | URL |
|------------------|---------|-----|
| **UserViewSet** | GET, PUT, PATCH | `/api/v1/users/users/` |
| **OperatorViewSet** | GET (list), GET (detail), POST | `/api/v1/users/operators/` |
| **DocumentViewSet** | GET, POST, PUT, DELETE | `/api/v1/users/documents/` |
| **NotificationViewSet** | GET (list), POST (mark_as_read) | `/api/v1/users/notifications/` |
| **send_otp** | POST | `/api/v1/users/auth/send-otp/` |
| **verify_otp** | POST | `/api/v1/users/auth/verify-otp/` |
| **register** | POST | `/api/v1/users/auth/register/` |

### Serializers (`apps/users/serializers.py`)
- `UserSerializer` - Full user details
- `UserProfileSerializer` - Public profile
- `OperatorSerializer` - Operator details (private)
- `OperatorPublicSerializer` - Operator public info
- `DocumentSerializer` - Document details
- `NotificationSerializer` - Notification details
- `OTPRequestSerializer` - OTP request validation
- `RegisterSerializer` - User registration

### URLs (`apps/users/urls.py`)
```python
/api/v1/users/
├── auth/
│   ├── send-otp/          # POST
│   ├── verify-otp/        # POST
│   └── register/          # POST
├── users/                 # UserViewSet
├── operators/             # OperatorViewSet
├── documents/             # DocumentViewSet
└── notifications/         # NotificationViewSet
```

---

## 🚌 APP: BUSES (`apps.buses`)

### Models (`apps/buses/models.py`)
| Model | Fields | Purpose |
|-------|--------|---------|
| **Bus** | id, operator, name, bus_type, ac_type, seating_capacity, price_per_km, city, approval_status | Bus inventory |
| **BusPhoto** | id, bus, image_url, is_primary | Bus images |
| **BusAmenity** | id, bus, amenity_name | Bus features (WiFi, AC, etc.) |
| **AvailabilityBlock** | id, bus, date, is_available, blocked_by_booking | Booking calendar |

#### Bus Key Fields
- `bus_type`: mini_bus / medium_bus / luxury_coach / tempo_traveller
- `ac_type`: ac / non_ac / both
- `fuel_type`: diesel / cng / electric
- `approval_status`: pending / approved / rejected
- `rating_avg`: Bus rating (0-5)
- `is_verified`: Admin verified

### Services (`apps/buses/services.py`)
| Service | Methods | Purpose |
|---------|---------|---------|
| **BusService** | `create_bus()`, `update_bus()`, `approve_bus()`, `search_buses()`, `check_availability()` | Bus management & search |

### Views (`apps/buses/views.py`)
| ViewSet | Methods | URL |
|---------|---------|-----|
| **BusViewSet** | GET, POST, PUT, PATCH, DELETE | `/api/v1/buses/` |
| **BusPhotoViewSet** | GET, POST, DELETE | `/api/v1/buses/{bus_id}/photos/` |
| **BusAmenityViewSet** | GET, POST, DELETE | `/api/v1/buses/{bus_id}/amenities/` |
| **AvailabilityBlockViewSet** | GET, POST, DELETE | `/api/v1/buses/{bus_id}/availability-blocks/` |

### Serializers (`apps/buses/serializers.py`)
- `BusSerializer` - Full bus details
- `BusListSerializer` - List view with operator info
- `BusSearchSerializer` - Search results
- `BusPhotoSerializer` - Photo upload/list
- `BusAmenitySerializer` - Amenity management
- `AvailabilityBlockSerializer` - Calendar management

### URLs (`apps/buses/urls.py`)
```python
/api/v1/buses/
├── /                                    # BusViewSet (list, create)
├── {id}/                                # BusViewSet (retrieve, update, delete)
├── {bus_id}/photos/                     # Photos (list, create)
├── {bus_id}/photos/{id}/                # Photo (delete)
├── {bus_id}/amenities/                  # Amenities (list, create)
└── {bus_id}/availability-blocks/        # Availability (list, create)
```

---

## 📝 APP: BOOKINGS (`apps.bookings`)

### Models (`apps/bookings/models.py`)
| Model | Fields | Purpose |
|-------|--------|---------|
| **Booking** | id, customer, operator, bus, booking_number, pickup_date, total_amount, status | Booking records |
| **Payment** | id, booking, amount, payment_mode, status, cashfree_order_id | Payment tracking |
| **BookingHistory** | id, booking, old_status, new_status, changed_by | Audit trail |
| **Coupon** | id, code, discount_type, value, usage_limit | Promo codes |
| **CouponUsage** | id, coupon, user, booking | Coupon redemption tracking |

#### Booking Key Fields
- `status`: pending / confirmed / in_progress / completed / cancelled_by_customer / cancelled_by_operator / expired
- `trip_type`: one_way / round_trip / multi_day
- `payment_mode`: online_full / online_advance / pay_driver
- `payment_status`: pending / advance_paid / fully_paid / refund_initiated / refunded
- `trip_status`: upcoming / ongoing / completed / cancelled

### Services (`apps/bookings/services.py`)
| Service | Methods | Purpose |
|---------|---------|---------|
| **BookingService** | `create_booking()`, `confirm_booking()`, `cancel_booking()`, `update_trip_status()` | Booking lifecycle |
| **PaymentService** | `create_payment()`, `capture_payment()`, `initiate_refund()`, `verify_webhook()` | Payment processing |
| **CouponService** | `validate_coupon()`, `apply_coupon()`, `create_coupon()` | Coupon management |

### Views (`apps/bookings/views.py`)
| ViewSet/Endpoint | Methods | URL |
|------------------|---------|-----|
| **BookingViewSet** | GET, POST, PUT, PATCH, DELETE | `/api/v1/bookings/` |
| **PaymentViewSet** | GET, POST | `/api/v1/bookings/payments/` |
| **CouponViewSet** | GET, POST, PUT, PATCH, DELETE | `/api/v1/bookings/coupons/` |
| **cashfree_webhook** | POST | `/api/v1/bookings/payments/webhook/` |
| **calculate_price** | POST | `/api/v1/bookings/calculate-price/` |
| **health_check** | GET | `/api/v1/bookings/health/` |

### Serializers (`apps/bookings/serializers.py`)
- `BookingSerializer` - Full booking details
- `BookingCreateSerializer` - Create new booking
- `BookingListSerializer` - List view
- `PaymentSerializer` - Payment details
- `CouponSerializer` - Coupon management
- `PriceCalculationSerializer` - Price calculator

### URLs (`apps/bookings/urls.py`)
```python
/api/v1/bookings/
├── health/                    # Health check
├── calculate-price/           # POST - Price calculator
├── /                          # BookingViewSet (list, create)
├── {id}/                      # BookingViewSet (retrieve, update, delete)
├── payments/                  # PaymentViewSet
├── payments/webhook/          # POST - Cashfree webhook
└── coupons/                   # CouponViewSet
```

---

## ⭐ APP: REVIEWS (`apps.reviews`)

### Models (`apps/reviews/models.py`)
| Model | Fields | Purpose |
|-------|--------|---------|
| **BusReview** | id, bus, customer, booking, rating_overall, rating_driver, rating_cleanliness, comment | Bus reviews |
| **OperatorReview** | id, operator, customer, booking, overall_rating, punctuality_rating, communication_rating | Operator reviews |

### Services (`apps/reviews/services.py`)
| Service | Methods | Purpose |
|---------|---------|---------|
| **ReviewService** | `create_bus_review()`, `create_operator_review()`, `approve_review()`, `flag_review()` | Review management |

### Views (`apps/reviews/views.py`)
| ViewSet | Methods | URL |
|---------|---------|-----|
| **BusReviewViewSet** | GET, POST, PUT, DELETE | `/api/v1/reviews/bus/` |
| **OperatorReviewViewSet** | GET, POST, PUT, DELETE | `/api/v1/reviews/operator/` |

### Serializers (`apps/reviews/serializers.py`)
- `BusReviewSerializer` - Bus review details
- `OperatorReviewSerializer` - Operator review details

### URLs (`apps/reviews/urls.py`)
```python
/api/v1/reviews/
├── bus/                # BusReviewViewSet
└── operator/           # OperatorReviewViewSet
```

---

## 🔔 APP: COMMON (`apps.common`)

### Notification Service (`apps/common/notification_service.py`)
| Class | Methods | Purpose |
|-------|---------|---------|
| **NotificationService** | `send_notification()`, `create_in_app_notification()` | Centralized notification system |

### Tasks (`apps/common/tasks.py`)
- `send_notification_task()` - Celery task for async notifications
- Integrates with n8n webhook for SMS/Email/WhatsApp via Brevo

### Authentication (`apps/common/authentication.py`)
- `BearerTokenAuthentication` - Token-based auth
- `TokenAuthentication` - DRF token auth

---

## 🗄️ DATABASE SCHEMA

### Tables Summary
| Table | Primary Key | Foreign Keys | Indexes |
|-------|-------------|--------------|---------|
| `users_customuser` | UUID | - | phone, role, city |
| `operator_documents` | UUID | user_id | user, bus, expiry_date |
| `notifications` | UUID | user_id | user + is_read |
| `buses_bus` | UUID | operator_id | operator, city, approval_status |
| `bus_photos` | UUID | bus_id | bus |
| `bus_amenities` | UUID | bus_id | bus |
| `availability_blocks` | UUID | bus_id | bus, date |
| `bookings_booking` | UUID | customer_id, operator_id, bus_id | customer, operator, bus, pickup_date, status, booking_number |
| `bookings_payment` | UUID | booking_id | booking, cashfree_order_id |
| `booking_history` | UUID | booking_id, changed_by | booking |
| `coupons` | UUID | created_by | code |
| `coupon_usage` | UUID | coupon_id, user_id, booking_id | coupon, user |
| `bus_reviews` | UUID | bus_id, customer_id, booking_id, operator_id | bus, customer, operator |
| `operator_reviews` | UUID | operator_id, customer_id, booking_id | operator, customer |

---

## 🔗 API ENDPOINTS QUICK REFERENCE

### Authentication
```
POST   /api/v1/users/auth/send-otp/
POST   /api/v1/users/auth/verify-otp/
POST   /api/v1/users/auth/register/
```

### Users
```
GET    /api/v1/users/users/              # List all users (admin)
GET    /api/v1/users/users/me/           # Current user profile
PUT    /api/v1/users/users/me/           # Update profile
GET    /api/v1/users/operators/          # List operators
POST   /api/v1/users/operators/          # Create operator
GET    /api/v1/users/documents/          # List documents
POST   /api/v1/users/documents/          # Upload document
GET    /api/v1/users/notifications/      # List notifications
POST   /api/v1/users/notifications/mark_as_read/
```

### Buses
```
GET    /api/v1/buses/                    # List/search buses
POST   /api/v1/buses/                    # Create bus (operator)
GET    /api/v1/buses/{id}/               # Bus details
PUT    /api/v1/buses/{id}/               # Update bus
DELETE /api/v1/buses/{id}/               # Delete bus
POST   /api/v1/buses/{id}/photos/        # Upload photo
POST   /api/v1/buses/{id}/amenities/     # Add amenity
GET    /api/v1/buses/{id}/availability-blocks/
```

### Bookings
```
GET    /api/v1/bookings/health/          # Health check
POST   /api/v1/bookings/calculate-price/ # Calculate price
GET    /api/v1/bookings/                 # List bookings
POST   /api/v1/bookings/                 # Create booking
GET    /api/v1/bookings/{id}/            # Booking details
PUT    /api/v1/bookings/{id}/            # Update booking
GET    /api/v1/bookings/payments/        # List payments
POST   /api/v1/bookings/payments/        # Create payment
POST   /api/v1/bookings/payments/webhook/ # Cashfree webhook
GET    /api/v1/bookings/coupons/         # List coupons
POST   /api/v1/bookings/coupons/validate/ # Validate coupon
```

### Reviews
```
GET    /api/v1/reviews/bus/              # List bus reviews
POST   /api/v1/reviews/bus/              # Create bus review
GET    /api/v1/reviews/operator/         # List operator reviews
POST   /api/v1/reviews/operator/         # Create operator review
```

---

## 🛠️ UTILITY SCRIPTS

### Location
`backend/scripts/`

| Script | Purpose |
|--------|---------|
| `check_error_codes.py` | Validate error code uniqueness |
| `stress_test_booking.py` | Load testing for bookings |
| `test_admin.py` | Admin interface testing |

---

## 📚 DOCUMENTATION FILES

### Location: `Docs/`

| File | Purpose |
|------|---------|
| **PRD.md** | Product Requirements Document |
| **CONTEXT.md** | Business context & market analysis |
| **SETUP.md** | Development environment setup |
| **PROJECT_STRUCTURE.md** | Project architecture |
| **ERROR_REGISTRY.md** | All error codes catalog |
| **TODO.md** | Development roadmap |
| **PRODUCTION_READY_STATUS.md** | Deployment checklist |
| **PHASE_PROMPTS.md** | Development phase guidelines |
| **TESTSPRITE_ANALYSIS.md** | Testing analysis |
| **N8N.md** | Automation workflows |

---

## 🔐 SECURITY FEATURES

### Authentication
- **Method**: Phone-based OTP (via Supabase)
- **Token**: DRF Token Authentication
- **Session**: JWT-style bearer tokens

### Authorization
- **Permissions**: Role-based (Customer, Operator, Admin)
- **Row-level**: Custom permissions per app
- **API**: Permission classes on every endpoint

### Data Protection
- **Encryption**: Field-level for bank_account, pan_number (Fernet)
- **Connection**: SSL for production database
- **Webhooks**: HMAC signature verification

### Security Headers (Production)
- `SECURE_SSL_REDIRECT=True`
- `SECURE_HSTS_SECONDS=31536000`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`

---

## 🚀 DEPLOYMENT CONFIGURATION

### Backend (Heroku)
| Config | Value |
|--------|-------|
| **Runtime** | Python 3.14 |
| **Server** | Gunicorn |
| **Database** | PostgreSQL (Supabase) |
| **Storage** | Cloudinary (media) |
| **Static** | WhiteNoise |

### Frontend (Vercel)
| Config | Value |
|--------|-------|
| **Framework** | Next.js 14 |
| **Build** | `npm run build` |
| **Deploy** | Auto on git push |

### Background Jobs
| Service | Purpose |
|---------|---------|
| **Celery** | Async tasks |
| **Redis** | Celery broker |
| **Celery Beat** | Scheduled tasks |

### Scheduled Tasks
- `expire_pending_bookings` - Hourly (expire 24hr old pending bookings)
- `send_trip_reminders` - Daily at 9am (notify upcoming trips)

---

## 🔌 THIRD-PARTY INTEGRATIONS

| Service | Purpose | Config Vars |
|---------|---------|-------------|
| **Supabase** | Database & Auth | `SUPABASE_URL`, `SUPABASE_KEY` |
| **Cloudinary** | Image storage | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` |
| **Cashfree** | Payment gateway | `CASHFREE_APP_ID`, `CASHFREE_SECRET_KEY` |
| **Brevo** | Email/WhatsApp | `BREVO_API_KEY`, `BREVO_WHATSAPP_SENDER` |
| **n8n** | Notification automation | `N8N_WEBHOOK_URL` |
| **Redis** | Task queue | `CELERY_BROKER_URL` |

---

## 🎯 QUICK NAVIGATION GUIDE

### I want to...

**Add a new model field:**
1. Update model in `apps/{app}/models.py`
2. Run `python manage.py makemigrations`
3. Run `python manage.py migrate`
4. Update serializer in `apps/{app}/serializers.py`

**Add a new API endpoint:**
1. Add view in `apps/{app}/views.py`
2. Add URL in `apps/{app}/urls.py`
3. Add permissions if needed
4. Update serializer if needed

**Modify business logic:**
1. Find service class in `apps/{app}/services.py`
2. Update service method
3. Update tests in `apps/{app}/tests.py`

**Add a new background task:**
1. Create task in `apps/{app}/tasks.py`
2. Add to `CELERY_BEAT_SCHEDULE` in settings
3. Test locally with Celery worker

**Debug an error:**
1. Check error code in `Docs/ERROR_REGISTRY.md`
2. Search codebase for error code (e.g., `USR-VIEWS-PERM-001`)
3. Check service layer for business logic

**Understand authentication:**
1. See `apps/common/authentication.py`
2. See `apps/users/services.py` → `AuthService`
3. See `apps/users/views.py` → `send_otp`, `verify_otp`

**Understand booking flow:**
1. `apps/bookings/services.py` → `BookingService.create_booking()`
2. `apps/bookings/views.py` → `BookingViewSet.create()`
3. `apps/bookings/tasks.py` → `send_booking_notification`

**Check payment integration:**
1. `apps/bookings/services.py` → `PaymentService`
2. `apps/bookings/views.py` → `cashfree_webhook`
3. Cashfree docs for API reference

**Review security rules:**
1. `.github/copilot-instructions.md` - FAANG-level security rules
2. `Docs/ERROR_REGISTRY.md` - All error codes
3. `apps/{app}/permissions.py` - Custom permissions

---

## 📊 KEY METRICS & MONITORING

### Database Indexes
- **Users**: phone, role, city
- **Buses**: operator, city, approval_status
- **Bookings**: customer, operator, bus, pickup_date, status, booking_number
- **Reviews**: bus, customer, operator

### Performance Targets
- API response time: <200ms
- Database query time: <100ms
- Frontend page load: <2s
- Error rate: <0.1%

### Health Checks
- `/api/v1/bookings/health/` - Backend health
- Database connection check
- Redis connection check

---

## 🧪 TESTING

### Test Files
| App | Test File | Command |
|-----|-----------|---------|
| **Users** | `apps/users/tests.py` | `python manage.py test apps.users` |
| **Buses** | `apps/buses/tests.py`, `tests_search.py` | `python manage.py test apps.buses` |
| **Bookings** | `apps/bookings/tests.py`, `tests_pricing.py` | `python manage.py test apps.bookings` |
| **Reviews** | `apps/reviews/tests.py` | `python manage.py test apps.reviews` |
| **Common** | `apps/common/tests_notifications.py` | `python manage.py test apps.common` |

### Run All Tests
```bash
cd backend
python manage.py test
```

---

## 📝 ERROR CODE FORMAT

```
[APP]-[FILE]-[TYPE]-[NUMBER]

APP:  USR, BUS, BOK, PAY, REV, DOC
FILE: MODELS, VIEWS, SERV, SERIAL
TYPE: VAL, PERM, AUTH, CONFLICT, DB, API
NUMBER: 001, 002, 003...

Example: BOK-SERV-VAL-008 (Booking Service Validation Error #8)
```

All error codes documented in: `Docs/ERROR_REGISTRY.md`

---

## 🎨 FRONTEND STRUCTURE

```
frontend/
├── app/                    # Next.js app directory
│   ├── dashboard/         # Dashboard pages
│   ├── login/             # Login page
│   ├── register/          # Registration
│   └── search/            # Bus search
├── components/            # React components
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   ├── store.ts          # State management
│   └── supabase.ts       # Supabase client
└── styles/               # CSS styles
```

---

## 🔍 SEARCH THIS INDEX

Use `Ctrl+F` / `Cmd+F` to search for:
- Model names (e.g., "CustomUser", "Booking")
- Endpoint URLs (e.g., "/api/v1/bookings/")
- Service methods (e.g., "create_booking")
- Error types (e.g., "BOK-SERV")
- File paths (e.g., "apps/users/views.py")

---

**END OF CODEBASE INDEX**

*This index is automatically accessible to GitHub Copilot for quick navigation and context.*
