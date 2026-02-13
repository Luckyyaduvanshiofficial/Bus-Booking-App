# DEPLOYMENT CHECKLIST - Bus Booking Platform

**Version:** 1.0 (Phase 1)  
**Last Updated:** 2026-02-13  
**Deployment Target:** Backend → Heroku | Frontend → Vercel

---

## PRE-DEPLOYMENT

### 1. Code Quality

- [ ] All 98 tests pass: `python manage.py test apps.users apps.buses apps.bookings apps.reviews --no-input`
- [ ] No migration conflicts: `python manage.py makemigrations --check --dry-run`
- [ ] Error code coverage check: `python scripts/check_error_codes.py`
- [ ] Admin panel smoke test: `python scripts/test_admin.py`
- [ ] No `DEBUG = True` in production settings
- [ ] No hardcoded secrets in source code

### 2. Environment Variables (Heroku)

Verify all required env vars are set:

```bash
heroku config --app <app-name>
```

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key (generate new for prod) | ✅ |
| `DEBUG` | Must be `False` | ✅ |
| `ALLOWED_HOSTS` | `<app-name>.herokuapp.com,yourdomain.com` | ✅ |
| `DATABASE_URL` | Auto-set by Heroku Postgres OR Supabase URL | ✅ |
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase service role key | ✅ |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | ✅ |
| `CLOUDINARY_API_KEY` | Cloudinary API key | ✅ |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | ✅ |
| `CASHFREE_APP_ID` | Cashfree app ID (PRODUCTION) | ✅ |
| `CASHFREE_SECRET_KEY` | Cashfree secret key (PRODUCTION) | ✅ |
| `CASHFREE_ENV` | `PRODUCTION` (not TEST) | ✅ |
| `UPSTASH_REDIS_URL` | Redis URL for caching/rate-limiting | ✅ |
| `CORS_ALLOWED_ORIGINS` | Frontend URL(s) | ✅ |

### 3. Database

- [ ] Run migrations: `python manage.py migrate --no-input`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Verify all 33 migrations applied: `python manage.py showmigrations`
- [ ] Static files collected: `python manage.py collectstatic --no-input`

---

## BACKEND DEPLOYMENT (Heroku)

### Step 1: Verify Procfile

```
web: gunicorn bus_booking.wsgi --log-file -
```

### Step 2: Verify runtime.txt

```
python-3.14.0
```

### Step 3: Deploy

```bash
# Login
heroku login

# Add remote (first time only)
heroku git:remote -a <app-name>

# Push
git push heroku main

# Run migrations
heroku run python manage.py migrate --app <app-name>

# Collect static
heroku run python manage.py collectstatic --no-input --app <app-name>

# Create superuser (first time)
heroku run python manage.py createsuperuser --app <app-name>
```

### Step 4: Post-Deploy Verification

```bash
# Check logs
heroku logs --tail --app <app-name>

# Verify health
curl https://<app-name>.herokuapp.com/api/docs/

# Verify admin
# Navigate to https://<app-name>.herokuapp.com/admin/
```

---

## FRONTEND DEPLOYMENT (Vercel)

### Step 1: Environment Variables

Set in Vercel dashboard → Project → Settings → Environment Variables:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<backend>.herokuapp.com/api/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |

### Step 2: Deploy

```bash
# Vercel auto-deploys from GitHub main branch
# OR manual deploy:
cd frontend
vercel --prod
```

### Step 3: Verify

- [ ] Home page loads
- [ ] Login / OTP flow works
- [ ] API calls reach backend (check CORS)

---

## POST-DEPLOYMENT CHECKS

### Critical Path Testing

- [ ] **Auth Flow:** Send OTP → Verify → Register → Login
- [ ] **Bus Search:** Public search returns results
- [ ] **Booking Flow:** Search → Select Bus → Create Booking → Operator Confirms
- [ ] **Payment Flow:** Initiate Payment → Cashfree redirect → Webhook confirmation
- [ ] **Admin Panel:** Login at `/admin/` → View models → Approve resources
- [ ] **API Docs:** Swagger UI loads at `/api/docs/`

### Security Checklist

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` is unique and not committed to git
- [ ] `ALLOWED_HOSTS` is restrictive (not `*`)
- [ ] HTTPS enforced (Heroku default)
- [ ] CORS origins limited to frontend domain only
- [ ] CSRF protection enabled
- [ ] Rate limiting active (Upstash Redis)
- [ ] No sensitive data in error responses (custom exception handler active)
- [ ] Admin panel is behind authentication

### Performance Checklist

- [ ] Database queries use `select_related` / `prefetch_related`
- [ ] Pagination enabled on all list endpoints
- [ ] Static files served via whitenoise / CDN
- [ ] Database connection pooling configured (Supabase Session Pooler)

---

## ROLLBACK PROCEDURE

```bash
# Heroku — rollback to previous release
heroku rollback --app <app-name>

# If migration needs reverting:
heroku run python manage.py migrate <app_name> <previous_migration_number> --app <app-name>
```

---

## MONITORING

- **Heroku Logs:** `heroku logs --tail --app <app-name>`
- **Error Tracking:** Search error codes in logs (e.g. `BOK-SERV-CONFLICT-001`)
- **Database:** Supabase Dashboard → SQL Editor / Logs
- **Uptime:** Heroku metrics or external ping service

---

## CONTACTS

| Role | Name | Action |
|---|---|---|
| Backend Dev | — | Heroku deploys, Django issues |
| Frontend Dev | — | Vercel deploys, Next.js issues |
| DB Admin | — | Supabase config, migrations |

---

**Deployment is complete when ALL checkboxes above are ticked.**
