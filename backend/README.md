# Bus Booking Platform API

This is a Django REST Framework API for the Bus Booking Platform.

## Setup Instructions

### 1. Prerequisites
- Python 3.11+
- PostgreSQL
- Redis (for Celery)

### 2. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create sample data (optional)
python manage.py shell
```

### 3. Running Development Server

```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`
Admin panel: `http://localhost:8000/admin`
API Schema: `http://localhost:8000/api/schema/`
API Docs: `http://localhost:8000/api/docs/`

### 4. Database Setup

```bash
# Create database
createdb bus_booking_db

# Run migrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser
```

### 5. Deployment to Heroku

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set DEBUG=False
heroku config:set DJANGO_SECRET_KEY=your-secret-key

# Deploy
git push heroku main

# Run migrations on Heroku
heroku run python manage.py migrate

# Create superuser on Heroku
heroku run python manage.py createsuperuser
```

## Project Structure

```
backend/
├── bus_booking/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── __init__.py
├── apps/
│   ├── users/            # User management (customers, operators)
│   ├── buses/            # Bus catalog
│   ├── bookings/         # Booking and payment management
│   ├── reviews/          # Ratings and reviews
│   └── __init__.py
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile              # Heroku deployment
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/send_otp` - Send OTP (via Supabase Auth)
- `POST /api/v1/users/verify_otp` - Verify OTP

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/update_profile` - Update profile
- `POST /api/v1/users/operators/register_as_operator` - Become operator

### Buses
- `GET /api/v1/buses` - List all buses
- `POST /api/v1/buses/search` - Search buses with filters
- `GET /api/v1/buses/{id}` - Get bus details
- `POST /api/v1/buses/` - Create bus (operators only)
- `GET /api/v1/buses/my_buses` - My buses (operators only)

### Bookings
- `POST /api/v1/bookings/create_booking` - Create booking
- `GET /api/v1/bookings/my_bookings` - My bookings
- `POST /api/v1/bookings/{id}/cancel` - Cancel booking
- `GET /api/v1/bookings/{id}/history` - Booking status history

### Payments
- `POST /api/v1/bookings/payments/initiate_payment` - Initiate payment
- `POST /api/v1/bookings/payments/{id}/confirm_payment` - Confirm payment

### Reviews
- `POST /api/v1/reviews/bus/create_review` - Create bus review
- `GET /api/v1/reviews/bus/bus_reviews` - Get bus reviews
- `POST /api/v1/reviews/operator/create_review` - Create operator review
- `GET /api/v1/reviews/operator/operator_reviews` - Get operator reviews

## Technologies Used

- Django 5.0
- Django REST Framework 3.14
- PostgreSQL
- Redis (Celery)
- Gunicorn
- Whitenoise (static files)
- Cashfree (payments)
- Supabase (auth, database)
- Cloudinary (image storage)

## Environment Variables

See `.env.example` for all required environment variables.

## Development Notes

1. Always use Django ORM instead of raw SQL
2. Follow REST API best practices
3. Write tests for critical features
4. Use serializers for validation
5. Implement proper error handling
6. Use ModelViewSets for standard CRUD operations

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Create pull request

## Support

For issues or questions, contact: [your-email]
