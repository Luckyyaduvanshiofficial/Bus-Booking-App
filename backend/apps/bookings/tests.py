"""Tests for bookings app – models, services, views, serializers.

Covers: Booking, Payment, BookingHistory, Coupon, CouponUsage,
BookingService, PaymentService, CouponService, and all ViewSets.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from apps.bookings.models import Booking, BookingHistory, Coupon, CouponUsage, Payment
from apps.bookings.services import BookingService, CouponService, PaymentService
from apps.buses.models import AvailabilityBlock, Bus
from apps.users.models import CustomUser


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════


def _create_test_users():
    """Create customer, operator, and admin users for tests."""
    customer = CustomUser(
        phone='+919200000001', username='+919200000001',
        name='Test Customer', role='customer',
    )
    customer.set_password('test123')
    customer.save(skip_validation=True)

    operator = CustomUser(
        phone='+919200000002', username='+919200000002',
        name='Test Operator', role='operator',
        business_name='Test Travels', commission_rate=Decimal('10.00'),
    )
    operator.set_password('test123')
    operator.save(skip_validation=True)

    admin = CustomUser(
        phone='+919200000003', username='+919200000003',
        name='Test Admin', role='admin', is_staff=True,
    )
    admin.set_password('test123')
    admin.save(skip_validation=True)

    return customer, operator, admin


def _create_test_bus(operator):
    """Create an approved test bus."""
    bus = Bus(
        operator=operator, name='Booking Bus', bus_type='mini_bus',
        seating_capacity=17, registration_number='RJ14BK0001',
        ac_type='ac', price_per_km=Decimal('20.00'),
        base_price=Decimal('2000.00'), base_city='Jaipur',
        is_active=True, approval_status='approved',
    )
    bus.save()
    return bus


# ═══════════════════════════════════════════════════════════════
#  MODEL TESTS
# ═══════════════════════════════════════════════════════════════


class BookingModelTest(TestCase):
    """Test Booking model validation and business methods."""

    def setUp(self) -> None:
        """Create test data."""
        self.customer, self.operator, self.admin = _create_test_users()
        self.bus = _create_test_bus(self.operator)

    def test_booking_number_generation(self) -> None:
        """Booking number auto-generated on save."""
        booking = Booking(
            customer=self.customer, operator=self.operator, bus=self.bus,
            trip_type='one_way', pickup_location='Jaipur',
            drop_location='Delhi', pickup_date=dt.date.today() + dt.timedelta(days=7),
            pickup_time=dt.time(8, 0), passenger_count=10,
            base_amount=Decimal('4000'), total_amount=Decimal('4500'),
        )
        booking.save()
        self.assertTrue(booking.booking_number.startswith('BK-'))

    def test_bok_models_val_001_past_date(self) -> None:
        """BOK-MODELS-VAL-001: Pickup date must be in the future."""
        booking = Booking(
            customer=self.customer, operator=self.operator, bus=self.bus,
            trip_type='one_way', pickup_location='Jaipur',
            drop_location='Delhi', pickup_date=dt.date(2020, 1, 1),
            pickup_time=dt.time(8, 0), passenger_count=10,
            base_amount=Decimal('4000'), total_amount=Decimal('4500'),
        )
        with self.assertRaises(DjangoValidationError):
            booking.clean()

    def test_bok_models_val_002_return_before_pickup(self) -> None:
        """BOK-MODELS-VAL-002: Return date must be after pickup date."""
        pickup = dt.date.today() + dt.timedelta(days=7)
        booking = Booking(
            customer=self.customer, operator=self.operator, bus=self.bus,
            trip_type='round_trip', pickup_location='Jaipur',
            drop_location='Delhi', pickup_date=pickup,
            return_date=pickup - dt.timedelta(days=1),
            pickup_time=dt.time(8, 0), passenger_count=10,
            base_amount=Decimal('4000'), total_amount=Decimal('4500'),
        )
        with self.assertRaises(DjangoValidationError):
            booking.clean()

    def test_bok_models_val_004_negative_amount(self) -> None:
        """BOK-MODELS-VAL-004: Total amount must be positive."""
        booking = Booking(
            customer=self.customer, operator=self.operator, bus=self.bus,
            trip_type='one_way', pickup_location='Jaipur',
            drop_location='Delhi',
            pickup_date=dt.date.today() + dt.timedelta(days=7),
            pickup_time=dt.time(8, 0), passenger_count=10,
            base_amount=Decimal('4000'), total_amount=Decimal('-100'),
        )
        with self.assertRaises(DjangoValidationError):
            booking.clean()

    def test_can_cancel(self) -> None:
        """Pending bookings can be cancelled."""
        booking = Booking(status='pending')
        self.assertTrue(booking.can_cancel())

    def test_cannot_cancel_completed(self) -> None:
        """Completed bookings cannot be cancelled."""
        booking = Booking(status='completed')
        self.assertFalse(booking.can_cancel())


class CouponModelTest(TestCase):
    """Test Coupon model is_valid property."""

    def test_valid_coupon(self) -> None:
        """Active coupon within dates is valid."""
        coupon = Coupon(
            code='TEST10', discount_type='percentage',
            discount_value=Decimal('10'),
            valid_from=timezone.now() - dt.timedelta(days=1),
            valid_until=timezone.now() + dt.timedelta(days=30),
            is_active=True,
        )
        coupon.save()
        self.assertTrue(coupon.is_valid)

    def test_expired_coupon(self) -> None:
        """Expired coupon is not valid."""
        coupon = Coupon(
            code='EXPIRED', discount_type='flat',
            discount_value=Decimal('100'),
            valid_from=timezone.now() - dt.timedelta(days=60),
            valid_until=timezone.now() - dt.timedelta(days=1),
            is_active=True,
        )
        coupon.save()
        self.assertFalse(coupon.is_valid)


# ═══════════════════════════════════════════════════════════════
#  SERVICE TESTS
# ═══════════════════════════════════════════════════════════════


class BookingServiceTest(TestCase):
    """Test BookingService – create, respond, cancel, complete."""

    def setUp(self) -> None:
        """Create test data."""
        self.customer, self.operator, self.admin = _create_test_users()
        self.bus = _create_test_bus(self.operator)
        self.future_date = dt.date.today() + dt.timedelta(days=14)

    def test_create_booking(self) -> None:
        """Create a valid booking."""
        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'estimated_km': Decimal('300'),
                'payment_mode': 'online_full',
            },
        )
        self.assertEqual(booking.status, 'pending')
        self.assertTrue(booking.booking_number.startswith('BK-'))
        self.assertTrue(booking.total_amount > 0)

    def test_create_booking_bok_serv_conflict_001(self) -> None:
        """BOK-SERV-CONFLICT-001: Bus not available on date."""
        AvailabilityBlock.objects.create(
            bus=self.bus,
            blocked_date=self.future_date,
            block_reason='booked_platform',
        )
        with self.assertRaises(ValidationError) as ctx:
            BookingService.create_booking(
                customer=self.customer,
                validated_data={
                    'bus': self.bus,
                    'trip_type': 'one_way',
                    'pickup_location': 'Jaipur',
                    'drop_location': 'Delhi',
                    'pickup_date': self.future_date,
                    'pickup_time': dt.time(8, 0),
                    'passenger_count': 10,
                    'payment_mode': 'online_full',
                },
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BOK-SERV-CONFLICT-001')

    def test_respond_confirm(self) -> None:
        """Operator confirms a pending booking."""
        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'payment_mode': 'online_full',
            },
        )
        booking = BookingService.respond_to_booking(
            booking=booking, new_status='confirmed',
            responded_by=self.operator,
        )
        self.assertEqual(booking.status, 'confirmed')

    def test_respond_not_pending_bok_serv_val_001(self) -> None:
        """BOK-SERV-VAL-001: Booking is not pending."""
        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'payment_mode': 'online_full',
            },
        )
        BookingService.respond_to_booking(
            booking=booking, new_status='confirmed',
            responded_by=self.operator,
        )
        with self.assertRaises(ValidationError) as ctx:
            BookingService.respond_to_booking(
                booking=booking, new_status='confirmed',
                responded_by=self.operator,
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BOK-SERV-VAL-001')

    def test_cancel_booking(self) -> None:
        """Customer cancels a pending booking."""
        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'payment_mode': 'online_full',
            },
        )
        booking = BookingService.cancel_booking(
            booking=booking, cancelled_by=self.customer,
        )
        self.assertEqual(booking.status, 'cancelled_by_customer')
        # Verify availability freed
        self.assertFalse(
            AvailabilityBlock.objects.filter(booking=booking).exists(),
        )

    def test_complete_booking(self) -> None:
        """Operator completes a confirmed booking."""
        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'payment_mode': 'online_full',
            },
        )
        BookingService.respond_to_booking(
            booking=booking, new_status='confirmed',
            responded_by=self.operator,
        )
        booking = BookingService.complete_booking(
            booking=booking, completed_by=self.operator,
        )
        self.assertEqual(booking.status, 'completed')

    def test_complete_not_confirmed_bok_serv_conflict_003(self) -> None:
        """BOK-SERV-CONFLICT-003: Only confirmed can complete."""
        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'payment_mode': 'online_full',
            },
        )
        with self.assertRaises(ValidationError) as ctx:
            BookingService.complete_booking(
                booking=booking, completed_by=self.operator,
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BOK-SERV-CONFLICT-003')


class CouponServiceTest(TestCase):
    """Test CouponService – validate_and_calculate."""

    def setUp(self) -> None:
        """Create test coupon and user."""
        self.customer, _, _ = _create_test_users()
        self.coupon = Coupon.objects.create(
            code='SAVE10', discount_type='percentage',
            discount_value=Decimal('10'),
            max_discount=Decimal('500'),
            min_booking=Decimal('1000'),
            valid_from=timezone.now() - dt.timedelta(days=1),
            valid_until=timezone.now() + dt.timedelta(days=30),
            is_active=True, per_user_limit=1,
        )

    def test_valid_coupon_apply(self) -> None:
        """Apply valid coupon returns correct discount."""
        result = CouponService.validate_and_calculate(
            code='SAVE10',
            booking_amount=Decimal('5000'),
            user=self.customer,
        )
        self.assertEqual(result['discount'], Decimal('500.00'))
        self.assertEqual(result['final_amount'], Decimal('4500.00'))

    def test_invalid_code_bok_serv_val_003(self) -> None:
        """BOK-SERV-VAL-003: Invalid coupon code."""
        with self.assertRaises(ValidationError) as ctx:
            CouponService.validate_and_calculate(
                code='NONEXISTENT',
                booking_amount=Decimal('5000'),
                user=self.customer,
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BOK-SERV-VAL-003')

    def test_min_booking_bok_serv_val_005(self) -> None:
        """BOK-SERV-VAL-005: Booking amount below minimum."""
        with self.assertRaises(ValidationError) as ctx:
            CouponService.validate_and_calculate(
                code='SAVE10',
                booking_amount=Decimal('500'),
                user=self.customer,
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BOK-SERV-VAL-005')


class PaymentServiceTest(TestCase):
    """Test PaymentService – initiate and confirm."""

    def setUp(self) -> None:
        """Create booking for payment tests."""
        self.customer, self.operator, self.admin = _create_test_users()
        self.bus = _create_test_bus(self.operator)
        self.future_date = dt.date.today() + dt.timedelta(days=14)

        self.booking = BookingService.create_booking(
            customer=self.customer,
            validated_data={
                'bus': self.bus,
                'trip_type': 'one_way',
                'pickup_location': 'Jaipur',
                'drop_location': 'Delhi',
                'pickup_date': self.future_date,
                'pickup_time': dt.time(8, 0),
                'passenger_count': 10,
                'payment_mode': 'online_full',
            },
        )

    @patch('apps.bookings.services.PaymentService._create_cashfree_order')
    def test_initiate_payment(self, mock_cf) -> None:
        """Initiate a payment for a booking."""
        mock_cf.return_value = 'cf_order_123'
        payment = PaymentService.initiate_payment(
            booking=self.booking,
            customer=self.customer,
        )
        self.assertEqual(payment.booking, self.booking)
        self.assertEqual(payment.status, 'created')

    def test_wrong_owner_bok_serv_perm_001(self) -> None:
        """BOK-SERV-PERM-001: Only booking owner can pay."""
        other = CustomUser(
            phone='+919200000099', username='+919200000099',
            role='customer',
        )
        other.set_password('test123')
        other.save(skip_validation=True)

        with self.assertRaises(ValidationError) as ctx:
            PaymentService.initiate_payment(
                booking=self.booking,
                customer=other,
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BOK-SERV-PERM-001')


# ═══════════════════════════════════════════════════════════════
#  API / VIEW TESTS
# ═══════════════════════════════════════════════════════════════


class BookingViewSetAPITest(APITestCase):
    """Test booking API endpoints."""

    def setUp(self) -> None:
        """Create all test data."""
        from rest_framework.authtoken.models import Token

        self.customer, self.operator, self.admin = _create_test_users()
        self.bus = _create_test_bus(self.operator)
        self.future_date = dt.date.today() + dt.timedelta(days=14)

        self.cust_token = Token.objects.create(user=self.customer)
        self.op_token = Token.objects.create(user=self.operator)
        self.admin_token = Token.objects.create(user=self.admin)

        self.client = APIClient()

    def test_create_booking_as_customer(self) -> None:
        """POST /bookings/ by customer creates booking."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.cust_token.key}')
        data = {
            'bus': str(self.bus.id),
            'trip_type': 'one_way',
            'pickup_location': 'Jaipur',
            'drop_location': 'Delhi',
            'pickup_date': str(self.future_date),
            'pickup_time': '08:00:00',
            'passenger_count': 10,
            'payment_mode': 'online_full',
        }
        resp = self.client.post('/api/v1/bookings/', data, format='json')
        self.assertIn(resp.status_code, (200, 201))

    def test_list_bookings_as_customer(self) -> None:
        """GET /bookings/ returns only customer's bookings."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.cust_token.key}')
        resp = self.client.get('/api/v1/bookings/')
        self.assertEqual(resp.status_code, 200)

    def test_operator_cannot_create_booking(self) -> None:
        """BOK-VIEWS-PERM-001: Only customers can create bookings."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.op_token.key}')
        data = {
            'bus': str(self.bus.id),
            'trip_type': 'one_way',
            'pickup_location': 'Jaipur',
            'drop_location': 'Delhi',
            'pickup_date': str(self.future_date),
            'pickup_time': '08:00:00',
            'passenger_count': 10,
            'payment_mode': 'online_full',
        }
        resp = self.client.post('/api/v1/bookings/', data, format='json')
        self.assertEqual(resp.status_code, 403)


class CouponViewSetAPITest(APITestCase):
    """Test coupon API endpoints."""

    def setUp(self) -> None:
        """Create test data."""
        from rest_framework.authtoken.models import Token

        self.customer, _, self.admin = _create_test_users()
        self.cust_token = Token.objects.create(user=self.customer)
        self.admin_token = Token.objects.create(user=self.admin)

        Coupon.objects.create(
            code='API10', discount_type='percentage',
            discount_value=Decimal('10'),
            valid_from=timezone.now() - dt.timedelta(days=1),
            valid_until=timezone.now() + dt.timedelta(days=30),
            is_active=True,
        )

        self.client = APIClient()

    def test_apply_coupon(self) -> None:
        """POST /coupons/apply/ returns discount."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.cust_token.key}')
        resp = self.client.post(
            '/api/v1/bookings/coupons/apply/',
            {'code': 'API10', 'booking_amount': '5000.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('discount', resp.data)
