# Bus Booking Platform - Project Structure

```
Bus Booking app/
│
├── CONTEXT.md                    # Business context & market analysis
├── PRD.md                        # Product requirements document
├── SETUP.md                      # Complete setup guide ⭐ START HERE
│
├── backend/                      # Django REST API
│   │
│   ├── bus_booking/              # Django project settings
│   │   ├── __init__.py
│   │   ├── settings.py           # ⚙️ Configuration (DB, installed apps, middlewares)
│   │   ├── urls.py               # 🔗 Main URL routing
│   │   ├── wsgi.py               # WSGI application
│   │   └── asgi.py               # ASGI application (future)
│   │
│   ├── apps/                     # Django applications
│   │   │
│   │   ├── __init__.py
│   │   │
│   │   ├── users/                # 👥 User Management
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py         # CustomUser, Document models
│   │   │   ├── serializers.py    # REST serializers
│   │   │   ├── views.py          # API viewsets
│   │   │   ├── urls.py           # API routes
│   │   │   ├── admin.py          # Django admin config
│   │   │   └── migrations/
│   │   │
│   │   ├── buses/                # 🚍 Bus Catalog
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py         # Bus, BusPhoto, BusAmenity, AvailabilityBlock
│   │   │   ├── serializers.py
│   │   │   ├── views.py          # Search, list, details endpoints
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   └── migrations/
│   │   │
│   │   ├── bookings/             # 📅 Bookings & Payments
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py         # Booking, Payment, BookingHistory
│   │   │   ├── serializers.py
│   │   │   ├── views.py          # Booking, payment endpoints
│   │   │   ├── urls.py
│   │   │   ├── admin.py
│   │   │   └── migrations/
│   │   │
│   │   └── reviews/              # ⭐ Ratings & Reviews
│   │       ├── __init__.py
│   │       ├── apps.py
│   │       ├── models.py         # BusReview, OperatorReview
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       ├── admin.py
│   │       └── migrations/
│   │
│   ├── manage.py                 # Django management script
│   ├── requirements.txt           # Python dependencies
│   ├── Procfile                  # Heroku deployment config
│   ├── runtime.txt               # Python 3.11.8
│   ├── .env.example              # Environment variables template
│   ├── .gitignore
│   ├── README.md                 # Backend documentation
│   └── static/                   # Static files (auto-collected)
│
├── frontend/                     # Next.js 14 PWA
│   │
│   ├── app/                      # Next.js App Router (pages)
│   │   │
│   │   ├── (auth)/               # Auth pages (grouped route)
│   │   │   ├── login/
│   │   │   │   └── page.tsx      # Login with OTP
│   │   │   └── register/
│   │   │       └── page.tsx      # User registration
│   │   │
│   │   ├── dashboard/
│   │   │   └── page.tsx          # User dashboard (protected)
│   │   │
│   │   ├── search/
│   │   │   └── page.tsx          # Bus search page
│   │   │
│   │   ├── my-bookings/
│   │   │   └── page.tsx          # Booking history (protected)
│   │   │
│   │   ├── profile/
│   │   │   └── page.tsx          # User profile (protected)
│   │   │
│   │   ├── operator/             # Operator routes (protected)
│   │   │   ├── buses/
│   │   │   │   └── page.tsx      # Manage buses
│   │   │   └── earnings/
│   │   │       └── page.tsx      # Earnings dashboard
│   │   │
│   │   ├── become-operator/
│   │   │   └── page.tsx          # Register as operator
│   │   │
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Home page
│   │   ├── providers.tsx         # App providers
│   │   └── globals.css           # Global styles
│   │
│   ├── components/               # Reusable React components
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── BusCard.tsx
│   │   ├── BookingForm.tsx
│   │   ├── ReviewCard.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── lib/                      # Utilities & helpers
│   │   ├── api.ts                # 🔗 Axios API client + endpoints
│   │   ├── supabase.ts           # 🔐 Supabase client
│   │   ├── store.ts              # 📦 Zustand state stores
│   │   ├── i18n.ts               # 🌐 Hindi + English translations
│   │   └── utils.ts              # Helper functions
│   │
│   ├── styles/
│   │   └── globals.css           # Tailwind + custom styles
│   │
│   ├── public/                   # Static assets
│   │   ├── favicon.ico
│   │   ├── manifest.json         # PWA manifest
│   │   ├── icon-192.png          # PWA icon
│   │   ├── icon-512.png
│   │   └── robots.txt
│   │
│   ├── package.json              # Dependencies
│   ├── tsconfig.json             # TypeScript config
│   ├── next.config.js            # Next.js config
│   ├── tailwind.config.js        # Tailwind config
│   ├── postcss.config.js         # PostCSS config
│   ├── .env.example              # Template
│   ├── .gitignore
│   ├── README.md                 # Frontend documentation
│   └── node_modules/             # Dependencies (auto-generated)
│
└── README.md                     # Main project README
```

---

## 📋 Key Files to Know

### Backend
- **`backend/bus_booking/settings.py`** - Configure database, apps, middleware, security
- **`backend/bus_booking/urls.py`** - Main API routing
- **`backend/apps/users/models.py`** - User model with roles (customer/operator/admin)
- **`backend/apps/buses/models.py`** - Bus listing and availability
- **`backend/apps/bookings/models.py`** - Booking and payment logic
- **`backend/.env.example`** - Copy and configure for your environment
- **`backend/requirements.txt`** - Install dependencies before running

### Frontend
- **`frontend/app/page.tsx`** - Home page (public)
- **`frontend/app/login/page.tsx`** - OTP-based login
- **`frontend/app/dashboard/page.tsx`** - User dashboard (protected)
- **`frontend/lib/api.ts`** - All API calls to backend
- **`frontend/lib/store.ts`** - Global state (auth, search, UI)
- **`frontend/.env.local`** - Copy from .env.example and add keys
- **`frontend/styles/globals.css`** - Tailwind + custom styles

---

## 🔧 Quick Reference

### Django Management
```bash
python manage.py migrate        # Apply database changes
python manage.py runserver      # Start dev server (port 8000)
python manage.py createsuperuser # Create admin account
python manage.py shell          # Interactive Python shell
python manage.py collectstatic  # Gather static files
```

### Next.js Development
```bash
npm run dev        # Start dev server (port 3000)
npm run build      # Build for production
npm run start      # Run production server
npm run lint       # Check code style
```

### Database
```bash
createdb bus_booking_db         # Create database
psql bus_booking_db             # Connect to database
python manage.py migrate        # Create tables
python manage.py makemigrations # Generate migration files
```

---

## 🚀 Development Workflow

1. **Start Backend**
   ```bash
   cd backend
   python manage.py runserver
   ```
   🟢 Available at http://localhost:8000

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```
   🟢 Available at http://localhost:3000

3. **Access Admin Panel**
   - URL: http://localhost:8000/admin
   - Use superuser credentials

4. **API Documentation**
   - URL: http://localhost:8000/api/docs

5. **Test Endpoints**
   - Use Postman or curl
   - Check `frontend/lib/api.ts` for endpoint list

---

## 📦 Dependencies

### Backend
- Django 5.0
- Django REST Framework 3.14
- PostgreSQL (psycopg2-binary)
- Supabase (Python SDK)
- Cashfree (payments)
- Pillow (images)
- Gunicorn (production)

### Frontend
- Next.js 14
- React 18
- Tailwind CSS
- Zustand (state)
- Axios (HTTP)
- Supabase Auth
- Leaflet (maps)
- react-hook-form

---

## 🌍 Deployment Targets

- **Frontend (Next.js):** Vercel (free tier available)
- **Backend (Django):** Heroku (with $320 free credits)
- **Database:** Heroku PostgreSQL or Supabase
- **Images:** Cloudinary (free tier available)
- **Authentication:** Supabase Auth (free)
- **Payments:** Cashfree (1.95% per transaction)

---

## ✅ MVP Scope (6-8 weeks)

### Included ✨
- Customer search and booking
- Operator registration and bus listing
- Payment processing (Cashfree)
- Ratings and reviews
- Both Hindi & English
- Admin panel
- PWA support

### Excluded (v2) 🔮
- Real-time chat
- Live GPS tracking
- AI-powered pricing
- Bulk booking dashboard
- Operator mobile app

---

## 📞 Getting Help

1. **Check SETUP.md** for detailed setup instructions
2. **Read PRD.md** for feature specifications
3. **Check Django docs** for backend issues
4. **Check Next.js docs** for frontend issues
5. **API errors?** Look at DRF error responses

---

## 🎯 Success Metrics

- [ ] Backend API fully functional
- [ ] Frontend connects to backend
- [ ] Authentication works (OTP)
- [ ] Search and booking flow complete
- [ ] Payments integrated
- [ ] Admin panel functional
- [ ] Deployed to Heroku + Vercel
- [ ] Mobile responsive

---

**Generated:** February 12, 2026  
**Status:** Ready to Build  
**Timeline:** 6-8 weeks to MVP
