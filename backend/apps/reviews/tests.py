"""Tests for reviews app – models, services, views, serializers.

Covers: BusReview, OperatorReview, ReviewService, and all ViewSets.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from apps.bookings.services import BookingService
from apps.buses.models import Bus
from apps.reviews.models import BusReview, OperatorReview
from apps.reviews.services import ReviewService
from apps.users.models import CustomUser


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════


def _create_users():
    """Create customer, operator, and admin."""
    customer = CustomUser(
        phone='+919300000001', username='+919300000001',
        name='Rev Customer', role='customer',
    )
    customer.set_password('test123')
    customer.save(skip_validation=True)

    operator = CustomUser(
        phone='+919300000002', username='+919300000002',
        name='Rev Operator', role='operator',
        is_verified=True, verification_status='verified',
        business_name='Rev Travels', commission_rate=Decimal('10.00'),
    )
    operator.set_password('test123')
    operator.save(skip_validation=True)

    admin = CustomUser(
        phone='+919300000003', username='+919300000003',
        name='Rev Admin', role='admin', is_staff=True,
    )
    admin.set_password('test123')
    admin.save(skip_validation=True)

    return customer, operator, admin


def _create_bus(operator):
    """Create approved bus."""
    bus = Bus(
        operator=operator, name='Review Bus', bus_type='mini_bus',
        seating_capacity=17, registration_number='RJ14RV0001',
        ac_type='ac', price_per_km=Decimal('20.00'),
        base_price=Decimal('2000.00'), base_city='Jaipur',
        is_active=True, approval_status='approved',
    )
    bus.save()
    return bus


def _create_completed_booking(customer, operator, bus):
    """Create a booking in completed status."""
    future_date = dt.date.today() + dt.timedelta(days=14)
    booking = BookingService.create_booking(
        customer=customer,
        validated_data={
            'bus': bus,
            'trip_type': 'one_way',
            'pickup_location': 'Jaipur',
            'drop_location': 'Delhi',
            'pickup_date': future_date,
            'pickup_time': dt.time(8, 0),
            'passenger_count': 10,
            'payment_mode': 'online_full',
        },
    )
    BookingService.respond_to_booking(
        booking=booking, new_status='confirmed',
        responded_by=operator,
    )
    BookingService.complete_booking(
        booking=booking, completed_by=operator,
    )
    return booking


# ═══════════════════════════════════════════════════════════════
#  MODEL TESTS
# ═══════════════════════════════════════════════════════════════


class BusReviewModelTest(TestCase):
    """Test BusReview model."""

    def setUp(self) -> None:
        self.customer, self.operator, self.admin = _create_users()
        self.bus = _create_bus(self.operator)
        self.booking = _create_completed_booking(
            self.customer, self.operator, self.bus,
        )

    def test_create_valid_review(self) -> None:
        """Create a valid bus review."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=5,
            review_text='Excellent bus with great amenities and comfort.',
        )
        self.assertEqual(review.rating_overall, 5)
        self.assertTrue(review.is_approved)

    def test_unapprove_review_resets_bus_rating_counters(self) -> None:
        """Bus aggregates should reset when approved review becomes unapproved."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=5,
            review_text='Excellent bus with great amenities and comfort.',
        )
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.rating_count, 1)

        review.is_approved = False
        review.save(update_fields=['is_approved'])

        self.bus.refresh_from_db()
        self.assertEqual(self.bus.rating_count, 0)
        self.assertEqual(self.bus.rating_avg, Decimal('0.0'))

    def test_rev_models_val_001_invalid_rating(self) -> None:
        """REV-MODELS-VAL-001: Rating must be between 1 and 5."""
        review = BusReview(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=6,
            review_text='Great bus with very comfortable seats.',
        )
        with self.assertRaises(DjangoValidationError):
            review.clean()

    def test_rev_models_val_002_short_comment(self) -> None:
        """REV-MODELS-VAL-002: Review text must be at least 10 characters."""
        review = BusReview(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=4,
            review_text='Short',
        )
        with self.assertRaises(DjangoValidationError):
            review.clean()


class OperatorReviewModelTest(TestCase):
    """Test OperatorReview model."""

    def setUp(self) -> None:
        self.customer, self.operator, _ = _create_users()

    def test_create_operator_review(self) -> None:
        """Create a valid operator review."""
        review = OperatorReview.objects.create(
            operator=self.operator,
            reviewer=self.customer,
            responsiveness_rating=4,
            professionalism_rating=5,
            reliability_rating=4,
            comment='Very professional operator with prompt service.',
        )
        self.assertEqual(review.operator, self.operator)
        self.assertIsNotNone(review.overall_rating)


# ═══════════════════════════════════════════════════════════════
#  SERVICE TESTS
# ═══════════════════════════════════════════════════════════════


class ReviewServiceTest(TestCase):
    """Test ReviewService."""

    def setUp(self) -> None:
        self.customer, self.operator, self.admin = _create_users()
        self.bus = _create_bus(self.operator)
        self.booking = _create_completed_booking(
            self.customer, self.operator, self.bus,
        )

    def test_moderate_approve(self) -> None:
        """Admin approves a review."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=5,
            review_text='Very comfortable bus with all amenities.',
        )
        ReviewService.moderate_review(review=review, action='approve')
        review.refresh_from_db()
        self.assertTrue(review.is_approved)
        self.assertFalse(review.is_flagged)

    def test_moderate_flag(self) -> None:
        """Admin flags a review."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=1,
            review_text='Absolutely terrible experience, never again!',
        )
        ReviewService.moderate_review(review=review, action='flag')
        review.refresh_from_db()
        self.assertTrue(review.is_flagged)

    def test_moderate_remove(self) -> None:
        """Admin removes a review."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=2,
            review_text='Some inappropriate content that should be removed.',
        )
        ReviewService.moderate_review(review=review, action='remove')
        review.refresh_from_db()
        self.assertFalse(review.is_approved)

    def test_moderate_invalid_action(self) -> None:
        """REV-SERV-VAL-001: Invalid moderation action."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=3,
            review_text='Average service but could improve considerably.',
        )
        with self.assertRaises(ValidationError) as ctx:
            ReviewService.moderate_review(review=review, action='invalid_action')
        self.assertEqual(ctx.exception.detail[0].code, 'REV-SERV-VAL-001')


# ═══════════════════════════════════════════════════════════════
#  API / VIEW TESTS
# ═══════════════════════════════════════════════════════════════


class BusReviewViewSetAPITest(APITestCase):
    """Test bus review API endpoints."""

    def setUp(self) -> None:
        from rest_framework.authtoken.models import Token

        self.customer, self.operator, self.admin = _create_users()
        self.bus = _create_bus(self.operator)
        self.booking = _create_completed_booking(
            self.customer, self.operator, self.bus,
        )

        self.cust_token = Token.objects.create(user=self.customer)
        self.admin_token = Token.objects.create(user=self.admin)
        self.client = APIClient()

    def test_create_bus_review(self) -> None:
        """POST /reviews/bus/ creates review."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.cust_token.key}')
        data = {
            'booking': str(self.booking.id),
            'rating_overall': 5,
            'review_text': 'Excellent bus with great amenities and comfort.',
        }
        resp = self.client.post('/api/v1/reviews/bus/', data, format='json')
        self.assertIn(resp.status_code, (200, 201))

    def test_list_bus_reviews(self) -> None:
        """GET /reviews/bus/ returns reviews (public)."""
        resp = self.client.get('/api/v1/reviews/bus/')
        self.assertEqual(resp.status_code, 200)

    def test_moderate_as_admin(self) -> None:
        """Admin can moderate bus reviews."""
        review = BusReview.objects.create(
            booking=self.booking,
            customer=self.customer,
            bus=self.bus,
            operator=self.operator,
            rating_overall=4,
            review_text='Good comfortable bus for long trips.',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        resp = self.client.post(
            f'/api/v1/reviews/bus/{review.id}/moderate/',
            {'action': 'approve'},
            format='json',
        )
        self.assertIn(resp.status_code, (200, 204))


class OperatorReviewViewSetAPITest(APITestCase):
    """Test operator review API endpoints."""

    def setUp(self) -> None:
        from rest_framework.authtoken.models import Token

        self.customer, self.operator, _ = _create_users()
        self.cust_token = Token.objects.create(user=self.customer)
        self.client = APIClient()

    def test_create_operator_review(self) -> None:
        """POST /reviews/operator/ creates review.

        Note: `reviewer` is set by perform_create from request.user,
        so it should NOT be in the payload.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.cust_token.key}')
        data = {
            'operator': str(self.operator.id),
            'responsiveness_rating': 4,
            'professionalism_rating': 5,
            'reliability_rating': 4,
            'comment': 'Very professional and helpful operator throughout.',
        }
        resp = self.client.post('/api/v1/reviews/operator/', data, format='json')
        self.assertIn(resp.status_code, (200, 201))

    def test_list_operator_reviews(self) -> None:
        """GET /reviews/operator/ returns reviews (public)."""
        resp = self.client.get('/api/v1/reviews/operator/')
        self.assertEqual(resp.status_code, 200)
