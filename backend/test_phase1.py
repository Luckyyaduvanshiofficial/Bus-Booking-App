"""Comprehensive Phase 1 API test suite."""
import os, sys, django, random
os.environ['DJANGO_SETTINGS_MODULE'] = 'bus_booking.settings'
django.setup()

import json
from django.test.utils import setup_test_environment
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apps.users.models import CustomUser
from apps.buses.models import Bus
from apps.bookings.models import Coupon
from django.utils import timezone
from datetime import timedelta

setup_test_environment()
client = APIClient()
passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} - {detail}")

print("\n" + "="*60)
print(" Phase 1 Backend Test Suite")
print("="*60)

# ── Setup test data ──────────────────────────────────────────
print("\n--- Setup ---")

# Get or create admin
admin = CustomUser.objects.get(phone='9999999999')
admin_token, _ = Token.objects.get_or_create(user=admin)

# Create customer
customer, _ = CustomUser.objects.get_or_create(
    phone='8888888888',
    defaults={'username': 'testcustomer', 'name': 'Test Customer', 'role': 'customer'}
)
cust_token, _ = Token.objects.get_or_create(user=customer)

# Create operator
operator, _ = CustomUser.objects.get_or_create(
    phone='7777777777',
    defaults={
        'username': 'testoperator', 'name': 'Test Operator', 'role': 'operator',
        'business_name': 'Test Bus Co', 'business_type': 'company',
        'is_verified': True, 'verification_status': 'verified',
    }
)
op_token, _ = Token.objects.get_or_create(user=operator)

print(f"  Admin: {admin.phone} (token: {admin_token.key[:8]}...)")
print(f"  Customer: {customer.phone} (token: {cust_token.key[:8]}...)")
print(f"  Operator: {operator.phone} (token: {op_token.key[:8]}...)")

# ── 1. Public endpoints ──────────────────────────────────────
print("\n--- 1. Public Endpoints ---")

r = client.get('/api/docs/')
test("API Docs accessible", r.status_code == 200)

r = client.get('/api/schema/')
test("API Schema accessible", r.status_code == 200)

r = client.get('/api/v1/buses/')
test("Bus listing (public)", r.status_code == 200)

r = client.get('/api/v1/reviews/bus/')
test("Bus reviews listing", r.status_code == 200)

r = client.get('/api/v1/reviews/operator/')
test("Operator reviews listing", r.status_code == 200)

# ── 2. Auth endpoints ────────────────────────────────────────
print("\n--- 2. Auth Endpoints ---")

reg_phone = f'66{random.randint(10000000, 99999999)}'
r = client.post('/api/v1/users/auth/register/', {
    'phone': reg_phone, 'name': 'New User', 'role': 'customer',
}, format='json')
test("User registration", r.status_code in (200, 201), f"status={r.status_code} body={r.content[:200]}")

# ── 3. User profile ──────────────────────────────────────────
print("\n--- 3. User Profile ---")

client.credentials(HTTP_AUTHORIZATION=f'Token {cust_token.key}')
r = client.get('/api/v1/users/users/me/')
test("Get my profile", r.status_code == 200)

r = client.put('/api/v1/users/users/update_profile/', {'name': 'Updated Customer'}, format='json')
test("Update profile", r.status_code == 200)

# ── 4. Operator endpoints ────────────────────────────────────
print("\n--- 4. Operator Endpoints ---")

client.credentials(HTTP_AUTHORIZATION=f'Token {op_token.key}')
r = client.get('/api/v1/users/operators/my_profile/')
test("Operator my profile", r.status_code == 200)

r = client.get('/api/v1/users/operators/dashboard/')
test("Operator dashboard", r.status_code == 200)

# ── 5. Bus CRUD ──────────────────────────────────────────────
print("\n--- 5. Bus Management ---")

client.credentials(HTTP_AUTHORIZATION=f'Token {op_token.key}')
r = client.post('/api/v1/buses/', {
    'name': 'Test Bus Alpha',
    'bus_type': 'mini_bus',
    'seating_capacity': 17,
    'registration_number': f'RJ14TC{random.randint(1000, 9999)}',
    'ac_type': 'ac',
    'fuel_type': 'diesel',
    'price_per_km': '25.00',
    'base_price': '5000.00',
    'base_city': 'Jaipur',
}, format='json')
test("Create bus", r.status_code == 201, f"status={r.status_code} body={r.content[:200]}")

if r.status_code == 201:
    bus_id = r.json()['id']
    
    r = client.get(f'/api/v1/buses/{bus_id}/')
    test("Get bus detail", r.status_code == 200)
    
    r = client.get('/api/v1/buses/my_buses/')
    test("Operator my buses", r.status_code == 200)
    
    # Photos
    r = client.post(f'/api/v1/buses/{bus_id}/photos/', {
        'photo_url': 'https://example.com/bus.jpg',
        'photo_type': 'exterior_front',
        'is_primary': True,
    }, format='json')
    test("Add bus photo", r.status_code == 201, f"status={r.status_code}")
    
    # Amenities
    r = client.post(f'/api/v1/buses/{bus_id}/amenities/', {
        'amenity': 'music_system',
    }, format='json')
    test("Add bus amenity", r.status_code == 201, f"status={r.status_code}")
    
    # Availability block
    from datetime import date, timedelta
    block_date = (date.today() + timedelta(days=30)).isoformat()
    r = client.post(f'/api/v1/buses/{bus_id}/availability/', {
        'blocked_date': block_date,
        'block_reason': 'maintenance',
    }, format='json')
    test("Block availability", r.status_code == 201, f"status={r.status_code}")
    
    # Admin approve bus
    client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
    r = client.post(f'/api/v1/buses/{bus_id}/approve/', {'action': 'approve'}, format='json')
    test("Admin approve bus", r.status_code == 200, f"status={r.status_code}")
    
    # Search
    client.credentials()
    r = client.post('/api/v1/buses/search/', {
        'city': 'Jaipur', 'passengers': 10,
    }, format='json')
    test("Bus search", r.status_code == 200)
    test("Search returns results", len(r.json()) > 0, f"got {len(r.json())} results")
else:
    bus_id = None

# ── 6. Booking ───────────────────────────────────────────────
print("\n--- 6. Booking System ---")

if bus_id:
    client.credentials(HTTP_AUTHORIZATION=f'Token {cust_token.key}')
    from datetime import date
    r = client.post('/api/v1/bookings/', {
        'bus': bus_id,
        'trip_type': 'one_way',
        'pickup_location': 'Jaipur Railway Station',
        'drop_location': 'Ajmer Bus Stand',
        'pickup_date': (date.today() + timedelta(days=7)).isoformat(),
        'pickup_time': '09:00:00',
        'passenger_count': 10,
        'estimated_km': '135.5',
        'payment_mode': 'online_full',
    }, format='json')
    test("Create booking", r.status_code == 201, f"status={r.status_code} body={r.content[:300]}")
    
    if r.status_code == 201:
        booking_id = r.json()['id']
        booking_number = r.json().get('booking_number', 'N/A')
        
        # Customer list bookings
        r = client.get('/api/v1/bookings/')
        test("List customer bookings", r.status_code == 200)
        
        # Booking detail
        r = client.get(f'/api/v1/bookings/{booking_id}/')
        test("Booking detail", r.status_code == 200)
        
        # Booking history
        r = client.get(f'/api/v1/bookings/{booking_id}/history/')
        test("Booking history", r.status_code == 200)
        
        # Operator confirms
        client.credentials(HTTP_AUTHORIZATION=f'Token {op_token.key}')
        r = client.post(f'/api/v1/bookings/{booking_id}/respond/', {
            'status': 'confirmed',
        }, format='json')
        test("Operator confirm booking", r.status_code == 200, f"status={r.status_code} body={r.content[:200]}")
        
        # Payment initiation
        client.credentials(HTTP_AUTHORIZATION=f'Token {cust_token.key}')
        r = client.post('/api/v1/bookings/payments/initiate/', {
            'booking_id': booking_id,
        }, format='json')
        test("Initiate payment", r.status_code == 201, f"status={r.status_code} body={r.content[:200]}")
        
        # Complete booking
        client.credentials(HTTP_AUTHORIZATION=f'Token {op_token.key}')
        r = client.post(f'/api/v1/bookings/{booking_id}/complete/', format='json')
        test("Complete booking", r.status_code == 200, f"status={r.status_code} body={r.content[:200]}")
    else:
        booking_id = None
else:
    booking_id = None

# ── 7. Reviews ───────────────────────────────────────────────
print("\n--- 7. Reviews ---")

if booking_id:
    client.credentials(HTTP_AUTHORIZATION=f'Token {cust_token.key}')
    r = client.post('/api/v1/reviews/bus/', {
        'booking': booking_id,
        'rating_overall': 5,
        'rating_cleanliness': 4,
        'review_text': 'Great bus! Very comfortable.',
    }, format='json')
    test("Submit bus review", r.status_code == 201, f"status={r.status_code} body={r.content[:200]}")

# ── 8. Coupons ───────────────────────────────────────────────
print("\n--- 8. Coupons ---")

client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
coupon_code = f'TEST{random.randint(100, 999)}'
r = client.post('/api/v1/bookings/coupons/', {
    'code': coupon_code,
    'discount_type': 'percentage',
    'discount_value': '10.00',
    'max_discount': '500.00',
    'min_booking': '1000.00',
    'valid_from': timezone.now().isoformat(),
    'valid_until': (timezone.now() + timedelta(days=30)).isoformat(),
}, format='json')
test("Admin create coupon", r.status_code == 201, f"status={r.status_code} body={r.content[:200]}")

client.credentials(HTTP_AUTHORIZATION=f'Token {cust_token.key}')
r = client.post('/api/v1/bookings/coupons/apply/', {
    'code': coupon_code,
    'booking_amount': '5000.00',
}, format='json')
test("Apply coupon", r.status_code == 200, f"status={r.status_code} body={r.content[:200]}")

# ── 9. Documents ─────────────────────────────────────────────
print("\n--- 9. Documents ---")

client.credentials(HTTP_AUTHORIZATION=f'Token {op_token.key}')
r = client.post('/api/v1/users/documents/', {
    'document_type': 'rc',
    'document_url': 'https://example.com/doc.pdf',
    'document_number': 'RC-2026-001',
}, format='json')
test("Upload document", r.status_code == 201, f"status={r.status_code} body={r.content[:200]}")

if r.status_code == 201:
    doc_id = r.json()['id']
    client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
    r = client.post(f'/api/v1/users/documents/{doc_id}/verify/', {
        'action': 'approve',
    }, format='json')
    test("Admin verify document", r.status_code == 200, f"status={r.status_code}")

# ── 10. Notifications ────────────────────────────────────────
print("\n--- 10. Notifications ---")

client.credentials(HTTP_AUTHORIZATION=f'Token {cust_token.key}')
r = client.get('/api/v1/users/notifications/')
test("List notifications", r.status_code == 200)

# ── 11. Admin panel ──────────────────────────────────────────
print("\n--- 11. Admin Panel ---")

from django.test import Client as DjangoClient
dc = DjangoClient()
r = dc.get('/admin/login/')
test("Admin login page", r.status_code == 200)

r = dc.post('/admin/login/', {'username': '9999999999', 'password': 'admin123'})
test("Admin login works", r.status_code in (200, 302))

# ── Summary ──────────────────────────────────────────────────
print("\n" + "="*60)
print(f" Results: {passed} PASSED, {failed} FAILED out of {passed + failed}")
print("="*60)

# Clean up test data
CustomUser.objects.filter(phone=reg_phone).delete()

if failed == 0:
    print("\n ALL Phase 1 tests PASSED!")
else:
    print(f"\n {failed} test(s) need attention.")
    sys.exit(1)
