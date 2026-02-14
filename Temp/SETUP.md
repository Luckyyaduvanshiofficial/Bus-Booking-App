# Complete Setup Guide - Bus Booking Platform

## 📋 Project Overview

**Bus Booking Platform** is a two-sided marketplace for private charter bus bookings in Rajasthan.

**Tech Stack:**
- **Frontend:** Next.js 14 (PWA) + Tailwind CSS + TypeScript
- **Backend:** Django 5 + Django REST Framework + PostgreSQL
- **Deployment:** Vercel (Frontend) + Heroku (Backend)
- **Auth:** Supabase Auth (OTP-based)
- **Payments:** Cashfree Payment Gateway
- **Images:** Cloudinary

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional, for Celery)
- Git

### Step 1: Clone & Setup Environment

```bash
# Create project directory
mkdir bus-booking
cd bus-booking

# Initialize git
git init

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Step 2: Configure Django

Edit `backend/.env`:
```
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
DB_NAME=bus_booking_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

### Step 3: Database Setup

```bash
# Create PostgreSQL database
createdb bus_booking_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Step 4: Frontend Setup

```bash
cd ../frontend
npm install
# Create .env.local
touch .env.local
```

Edit `frontend/.env.local`:
```
NEXT_PUBLIC_BACKEND_API=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-key
```

Start development server:
```bash
npm run dev
```

Access:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs
- **Admin Panel:** http://localhost:8000/admin

---

## 📁 Project Structure

```
bus-booking/
├── backend/
│   ├── bus_booking/          # Django project config
│   │   ├── settings.py       # Configuration
│   │   ├── urls.py           # URL routing
│   │   ├── wsgi.py           # WSGI app
│   │   └── __init__.py
│   │
│   ├── apps/
│   │   ├── users/            # User models & auth
│   │   ├── buses/            # Bus catalog
│   │   ├── bookings/         # Bookings & payments
│   │   └── reviews/          # Ratings & reviews
│   │
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile              # Heroku config
│   ├── runtime.txt           # Python version
│   └── README.md
│
├── frontend/
│   ├── app/                  # Next.js pages
│   │   ├── (auth)/           # Login/Register
│   │   ├── dashboard/
│   │   ├── search/
│   │   ├── my-bookings/
│   │   ├── operator/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/           # Reusable components
│   ├── lib/
│   │   ├── api.ts           # API client
│   │   ├── supabase.ts      # Auth client
│   │   ├── store.ts         # State management
│   │   └── i18n.ts          # Translations
│   │
│   ├── styles/
│   │   └── globals.css
│   │
│   ├── public/              # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   └── README.md
│
├── README.md
└── SETUP.md (this file)
```

---

## 🏗️ Backend Architecture

### Django Apps

#### 1. **Users App** (`apps/users/`)
- CustomUser model (phone-based authentication)
- Customer, Operator, Admin roles
- Document verification
- Profile management

**Main Files:**
- `models.py` - CustomUser, Document models
- `serializers.py` - REST serializers
- `views.py` - API viewsets
- `admin.py` - Django admin configuration

#### 2. **Buses App** (`apps/buses/`)
- Bus catalog and availability
- Bus photos and amenities
- Availability blocking

**Main Files:**
- `models.py` - Bus, BusPhoto, BusAmenity, AvailabilityBlock
- `serializers.py` - Bus serializers
- `views.py` - Search and listing endpoints
- `admin.py` - Admin configuration

#### 3. **Bookings App** (`apps/bookings/`)
- Booking creation and management
- Payment integration (Cashfree)
- Booking history and status tracking

**Main Files:**
- `models.py` - Booking, Payment, BookingHistory
- `serializers.py` - Booking serializers
- `views.py` - Booking and payment endpoints
- `admin.py` - Admin configuration

#### 4. **Reviews App** (`apps/reviews/`)
- Bus reviews and ratings
- Operator reviews

**Main Files:**
- `models.py` - BusReview, OperatorReview
- `serializers.py` - Review serializers
- `views.py` - Review endpoints
- `admin.py` - Admin configuration

---

## 🎨 Frontend Structure

### Pages

| Route | Purpose |
|-------|---------|
| `/` | Home page |
| `/login` | OTP-based login |
| `/register` | User registration |
| `/dashboard` | User dashboard |
| `/search` | Bus search |
| `/my-bookings` | Booking history |
| `/profile` | User profile |
| `/operator/buses` | Operator bus management |
| `/become-operator` | Register as operator |

### State Management (Zustand)

```typescript
// Authentication
useAuthStore() → { user, isLoggedIn, setUser, logout }

// Search filters
useSearchStore() → { fromLocation, toLocation, ... }

// UI settings
useUIStore() → { language, sidebarOpen, ... }
```

### API Client

```typescript
// Usage
API.buses.list()
API.bookings.create(data)
API.payments.initiate(data)
API.reviews.createBusReview(data)
```

---

## 📡 API Endpoints

### Authentication
```
POST   /api/v1/users/register
POST   /api/v1/users/send_otp
POST   /api/v1/users/verify_otp
GET    /api/v1/users/me
```

### Buses
```
GET    /api/v1/buses
POST   /api/v1/buses/search
GET    /api/v1/buses/{id}
POST   /api/v1/buses
GET    /api/v1/buses/my_buses
```

### Bookings
```
POST   /api/v1/bookings/create_booking
GET    /api/v1/bookings/my_bookings
POST   /api/v1/bookings/{id}/cancel
GET    /api/v1/bookings/{id}/history
```

### Payments
```
POST   /api/v1/bookings/payments/initiate_payment
POST   /api/v1/bookings/payments/{id}/confirm_payment
```

### Reviews
```
POST   /api/v1/reviews/bus/create_review
GET    /api/v1/reviews/bus/bus_reviews
POST   /api/v1/reviews/operator/create_review
```

---

## 🔐 Environment Variables

### Backend (`.env`)

```
# Django
DEBUG=False
DJANGO_SECRET_KEY=your-random-secret-key

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=bus_booking_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=db.example.com
DB_PORT=5432

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Cashfree
CASHFREE_APP_ID=your-app-id
CASHFREE_SECRET_KEY=your-secret-key

# MSG91
MSG91_API_KEY=your-api-key

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Frontend (`.env.local`)

```
NEXT_PUBLIC_BACKEND_API=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## 🌐 Deployment

### Deploy Backend to Heroku

```bash
cd backend

# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set env vars
heroku config:set DEBUG=False
heroku config:set DJANGO_SECRET_KEY=your-secret-key
heroku config:set SUPABASE_URL=your-supabase-url
heroku config:set SUPABASE_KEY=your-supabase-key
# ... set other vars

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

### Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in dashboard
NEXT_PUBLIC_BACKEND_API=https://your-heroku-app.herokuapp.com
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## 🔧 Development Commands

### Backend

```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Frontend

```bash
# Development
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint
```

---

## 📚 Implementation Checklist

### Phase 1: Backend Development
- [ ] User authentication (Supabase Auth)
- [ ] Bus management CRUD
- [ ] Search and filtering
- [ ] Booking creation and payment
- [ ] Reviews and ratings
- [ ] Admin panel

### Phase 2: Frontend Development
- [ ] Authentication pages (login/register)
- [ ] Home and search pages
- [ ] Bus listing and details
- [ ] Booking flow
- [ ] User dashboard
- [ ] Operator dashboard
- [ ] Reviews and ratings UI

### Phase 3: Integration
- [ ] Connect frontend to backend API
- [ ] Cashfree payment integration
- [ ] Cloudinary image uploads
- [ ] Email and SMS notifications
- [ ] Testing

### Phase 4: Deployment
- [ ] Deploy backend to Heroku
- [ ] Deploy frontend to Vercel
- [ ] Configure custom domains
- [ ] Set up monitoring and logging
- [ ] Production testing

---

## ❓ Troubleshooting

### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
psql --version

# Create database manually
createdb bus_booking_db

# Verify connection in .env
```

### Migration Errors
```bash
# Reset database (⚠️ deletes data)
python manage.py migrate zero

# Or recreate
dropdb bus_booking_db
createdb bus_booking_db
python manage.py migrate
```

### Frontend Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📖 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/)
- [Supabase](https://supabase.io/)
- [Cashfree API](https://www.cashfree.com/)

---

## 🎯 Next Steps

1. **Complete backend setup** - Make sure all migrations run successfully
2. **Connect Supabase** - Set up phone authentication
3. **Add Cloudinary** - For image hosting
4. **Integrate Cashfree** - Payment processing
5. **Build operator flows** - Bus registration and management
6. **Add notifications** - SMS via MSG91
7. **Deploy to production** - Follow deployment guide

---

## 💡 Tips

- Use Django admin panel for quick testing: `http://localhost:8000/admin`
- API documentation available at: `http://localhost:8000/api/docs`
- Test OTP flow with real Supabase setup
- Monitor Heroku logs: `heroku logs --tail`
- Check Next.js build errors in terminal output
- Use Postman to test API endpoints during development

---

## 📞 Support

For issues, questions, or contributions:
- Check existing issues in GitHub
- Create a new issue with details
- Join development discussions

---

**Last Updated:** February 12, 2026
**Status:** Ready to Build (6-8 weeks to MVP)
