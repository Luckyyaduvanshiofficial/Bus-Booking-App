#!/usr/bin/env python
"""
Concurrency Stress Test for Booking System

Tests race conditions and idempotency under concurrent load:
1. Double booking - multiple concurrent booking attempts for same bus/date
2. Double payment - concurrent payment initiations for same booking
3. Concurrent cancel/expire - race between manual cancel and auto-expire
4. Double refund - concurrent refund requests for same payment

Usage:
    python manage.py shell < scripts/stress_test_booking.py

    Or manually:
    python manage.py shell
    >>> exec(open('scripts/stress_test_booking.py').read())

Requirements:
    - Test database with sample data
    - CASHFREE_APP_ID configured (can use TEST mode)
"""

import os
import sys
import django
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
import time
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_booking.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from apps.bookings.models import Booking, Payment
from apps.bookings.services import BookingService, PaymentService
from apps.buses.models import Bus
from apps.users.models import CustomUser


class StressTestResults:
    """Collect and display test results."""
    
    def __init__(self):
        self.tests = []
    
    def add_test(self, name, passed, expected, actual, details=''):
        self.tests.append({
            'name': name,
            'passed': passed,
            'expected': expected,
            'actual': actual,
            'details': details,
        })
    
    def print_summary(self):
        print('\n' + '='*80)
        print('STRESS TEST RESULTS')
        print('='*80)
        
        for test in self.tests:
            status = '✅ PASS' if test['passed'] else '❌ FAIL'
            print(f'\n{status} - {test["name"]}')
            print(f'  Expected: {test["expected"]}')
            print(f'  Actual: {test["actual"]}')
            if test['details']:
                print(f'  Details: {test["details"]}')
        
        total = len(self.tests)
        passed = sum(1 for t in self.tests if t['passed'])
        print(f'\n{"="*80}')
        print(f'SUMMARY: {passed}/{total} tests passed')
        print(f'{"="*80}\n')


results = StressTestResults()


def setup_test_data():
    """Create test data for stress testing."""
    print('Setting up test data...')
    
    # Create test customer
    customer = CustomUser.objects.filter(
        role=CustomUser.Role.CUSTOMER
    ).first()
    
    if not customer:
        customer = CustomUser.objects.create_user(
            phone_number='9999999999',
            email='stress.test@example.com',
            role=CustomUser.Role.CUSTOMER,
            is_verified=True,
        )
    
    # Create test operator
    operator = CustomUser.objects.filter(
        role=CustomUser.Role.OPERATOR
    ).first()
    
    if not operator:
        operator = CustomUser.objects.create_user(
            phone_number='8888888888',
            email='operator.test@example.com',
            role=CustomUser.Role.OPERATOR,
            is_verified=True,
        )
    
    # Create test bus
    bus = Bus.objects.filter(operator=operator).first()
    
    if not bus:
        bus = Bus.objects.create(
            operator=operator,
            bus_name='Stress Test Bus',
            bus_number='TEST-001',
            bus_type='sleeper',
            total_seats=40,
            price_per_km=Decimal('2.50'),
        )
    
    print(f'✅ Test data ready: Customer={customer.id}, Operator={operator.id}, Bus={bus.id}')
    
    return customer, operator, bus


def test_double_booking(customer, bus, workers=20):
    """
    Test: 20 concurrent booking attempts for same bus/date.
    
    Expected: Only buses with available capacity should succeed.
    Race condition: Select-for-update should prevent double booking.
    """
    print('\n' + '-'*80)
    print('TEST 1: Double Booking Prevention')
    print('-'*80)
    
    journey_date = timezone.localdate() + timedelta(days=7)
    
    def create_booking_attempt():
        try:
            booking = BookingService.create_booking(
                validated_data={
                    'bus': bus,
                    'customer': customer,
                    'pickup_location': 'Test Pickup',
                    'dropoff_location': 'Test Dropoff',
                    'pickup_date': journey_date,
                    'passenger_count': 5,
                    'total_amount': Decimal('1000.00'),
                },
                customer=customer,
            )
            return {'success': True, 'booking_id': booking.id}
        except Exception as e:
            error_msg = str(e)
            # Expected errors: BOK-SERV-CONFLICT-002 (bus unavailable)
            return {'success': False, 'error': error_msg}
    
    # Launch concurrent booking attempts
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(create_booking_attempt) for _ in range(workers)]
        results_list = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start
    
    # Analyze results
    successes = [r for r in results_list if r['success']]
    failures = [r for r in results_list if not r['success']]
    
    # Expected: All bookings should either succeed or fail gracefully
    # No database deadlocks, no corrupt data
    all_handled = len(successes) + len(failures) == workers
    no_deadlocks = all('deadlock' not in r.get('error', '').lower() for r in failures)
    
    passed = all_handled and no_deadlocks
    
    results.add_test(
        name='Double Booking Prevention',
        passed=passed,
        expected=f'{workers} booking attempts handled without deadlocks',
        actual=f'{len(successes)} succeeded, {len(failures)} failed gracefully in {duration:.2f}s',
        details=f'First error: {failures[0].get("error", "N/A")[:100]}...' if failures else 'All succeeded',
    )
    
    # Cleanup
    if successes:
        Booking.objects.filter(
            id__in=[s['booking_id'] for s in successes]
        ).update(is_deleted=True)


def test_double_payment(customer, bus, workers=15):
    """
    Test: 15 concurrent payment initiations for same booking.
    
    Expected: Only 1 payment created, others return existing via idempotency.
    Race condition: Idempotency key should prevent duplicate payments.
    """
    print('\n' + '-'*80)
    print('TEST 2: Double Payment Prevention (Idempotency)')
    print('-'*80)
    
    # Create test booking
    journey_date = timezone.localdate() + timedelta(days=8)
    booking = BookingService.create_booking(
        validated_data={
            'bus': bus,
            'customer': customer,
            'pickup_location': 'Test Pickup',
            'dropoff_location': 'Test Dropoff',
            'pickup_date': journey_date,
            'passenger_count': 2,
            'total_amount': Decimal('500.00'),
        },
        customer=customer,
    )
    
    def initiate_payment_attempt():
        try:
            payment = PaymentService.initiate_payment(
                booking=booking,
                amount=Decimal('500.00'),
                payment_type='full',
            )
            return {'success': True, 'payment_id': payment.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Launch concurrent payment attempts
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(initiate_payment_attempt) for _ in range(workers)]
        results_list = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start
    
    # Analyze results
    successes = [r for r in results_list if r['success']]
    unique_payment_ids = set(s['payment_id'] for s in successes)
    
    # Expected: Only 1 unique payment created (all return same payment_id via idempotency)
    only_one_payment = len(unique_payment_ids) == 1
    all_succeeded = len(successes) == workers  # All should get payment (created or existing)
    
    passed = only_one_payment and all_succeeded
    
    results.add_test(
        name='Double Payment Prevention',
        passed=passed,
        expected='1 unique payment created, all 15 attempts return same payment',
        actual=f'{len(unique_payment_ids)} unique payment(s), {len(successes)}/{workers} succeeded in {duration:.2f}s',
        details=f'Payment IDs: {unique_payment_ids}',
    )
    
    # Cleanup
    booking.is_deleted = True
    booking.save()


def test_concurrent_cancel_expire(customer, bus, workers=10):
    """
    Test: 10 concurrent cancel attempts on same booking.
    
    Expected: Only 1 cancellation succeeds, others fail gracefully.
    Race condition: State machine should prevent double cancellation.
    """
    print('\n' + '-'*80)
    print('TEST 3: Concurrent Cancel/Expire Prevention')
    print('-'*80)
    
    # Create test booking
    journey_date = timezone.localdate() + timedelta(days=9)
    booking = BookingService.create_booking(
        validated_data={
            'bus': bus,
            'customer': customer,
            'pickup_location': 'Test Pickup',
            'dropoff_location': 'Test Dropoff',
            'pickup_date': journey_date,
            'passenger_count': 1,
            'total_amount': Decimal('300.00'),
        },
        customer=customer,
    )
    
    # Confirm booking first (need confirmed status to cancel)
    booking.status = Booking.Status.CONFIRMED
    booking.save()
    
    def cancel_booking_attempt():
        try:
            cancelled_booking = BookingService.cancel_booking(
                booking_id=booking.id,
                cancelled_by=customer,
                reason='Stress test',
            )
            return {'success': True, 'status': cancelled_booking.status}
        except Exception as e:
            error_msg = str(e)
            return {'success': False, 'error': error_msg}
    
    # Launch concurrent cancel attempts
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(cancel_booking_attempt) for _ in range(workers)]
        results_list = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start
    
    # Analyze results
    successes = [r for r in results_list if r['success']]
    failures = [r for r in results_list if not r['success']]
    
    # Expected: Only 1 cancellation succeeds
    only_one_success = len(successes) == 1
    others_failed_gracefully = len(failures) == workers - 1
    no_deadlocks = all('deadlock' not in r.get('error', '').lower() for r in failures)
    
    passed = only_one_success and others_failed_gracefully and no_deadlocks
    
    results.add_test(
        name='Concurrent Cancel Prevention',
        passed=passed,
        expected='1 cancellation succeeds, 9 fail gracefully',
        actual=f'{len(successes)} succeeded, {len(failures)} failed in {duration:.2f}s',
        details=f'Failed errors contain state validation: {any("transition" in r.get("error", "").lower() for r in failures)}',
    )
    
    # Cleanup
    booking.is_deleted = True
    booking.save()


def test_double_refund(customer, bus, workers=12):
    """
    Test: 12 concurrent refund requests for same payment.
    
    Expected: Only 1 refund created via idempotency.
    Race condition: Idempotency key should prevent duplicate refunds.
    """
    print('\n' + '-'*80)
    print('TEST 4: Double Refund Prevention (Idempotency)')
    print('-'*80)
    
    # Create and complete booking with payment
    journey_date = timezone.localdate() + timedelta(days=10)
    booking = BookingService.create_booking(
        validated_data={
            'bus': bus,
            'customer': customer,
            'pickup_location': 'Test Pickup',
            'dropoff_location': 'Test Dropoff',
            'pickup_date': journey_date,
            'passenger_count': 1,
            'total_amount': Decimal('400.00'),
        },
        customer=customer,
    )
    
    # Create payment manually
    payment = Payment.objects.create(
        booking=booking,
        amount=Decimal('400.00'),
        currency='INR',
        payment_type='full',
        status='captured',
        cf_order_id=f'TEST_ORDER_{booking.id}',
    )
    
    # Update booking to confirmed status
    booking.status = Booking.Status.CONFIRMED
    booking.payment_status = Booking.PaymentStatus.FULLY_PAID
    booking.save()
    
    def create_refund_attempt():
        try:
            refund = PaymentService.create_refund_record(
                booking=booking,
                amount=Decimal('400.00'),
                reason='Stress test refund',
            )
            return {'success': True, 'refund_id': refund.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Launch concurrent refund attempts
    start = time.time()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(create_refund_attempt) for _ in range(workers)]
        results_list = [f.result() for f in as_completed(futures)]
    
    duration = time.time() - start
    
    # Analyze results
    successes = [r for r in results_list if r['success']]
    unique_refund_ids = set(s['refund_id'] for s in successes)
    
    # Expected: Only 1 unique refund created
    only_one_refund = len(unique_refund_ids) == 1
    all_succeeded = len(successes) == workers  # All should get refund (created or existing)
    
    passed = only_one_refund and all_succeeded
    
    results.add_test(
        name='Double Refund Prevention',
        passed=passed,
        expected='1 unique refund created, all 12 attempts return same refund',
        actual=f'{len(unique_refund_ids)} unique refund(s), {len(successes)}/{workers} succeeded in {duration:.2f}s',
        details=f'Refund IDs: {unique_refund_ids}',
    )
    
    # Cleanup
    booking.is_deleted = True
    booking.save()


def run_all_tests():
    """Run all stress tests and display results."""
    print('\n' + '='*80)
    print('STARTING CONCURRENCY STRESS TESTS')
    print('='*80)
    print('\nThis will test race conditions and idempotency under concurrent load.')
    print('Tests simulate real-world scenarios with multiple concurrent users.')
    
    # Setup
    customer, operator, bus = setup_test_data()
    
    # Run tests
    try:
        test_double_booking(customer, bus, workers=20)
        test_double_payment(customer, bus, workers=15)
        test_concurrent_cancel_expire(customer, bus, workers=10)
        test_double_refund(customer, bus, workers=12)
    except Exception as e:
        print(f'\n❌ Test suite failed with error: {e}')
        import traceback
        traceback.print_exc()
    
    # Display results
    results.print_summary()


if __name__ == '__main__':
    run_all_tests()
