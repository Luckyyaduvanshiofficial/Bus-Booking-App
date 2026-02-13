"""Business logic for bookings, payments, and coupons.

All multi-step operations use @transaction.atomic.
Raises ValidationError for invalid data.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.bookings.models import (
    Booking,
    BookingHistory,
    Coupon,
    CouponUsage,
    Payment,
)
from apps.buses.models import AvailabilityBlock, Bus
from apps.users.models import CustomUser

logger = logging.getLogger(__name__)


class BookingService:
    """Handles booking creation, status transitions, and completion."""

    @staticmethod
    @transaction.atomic
    def create_booking(
        *,
        customer: CustomUser,
        validated_data: dict,
    ) -> Booking:
        """Create a new booking with pricing calculation and date blocking.

        Args:
            customer: The authenticated customer placing the booking.
            validated_data: Serializer-validated booking data.

        Returns:
            The newly created Booking instance.

        Raises:
            ValidationError: If the bus is not available on the selected date.
        """
        bus: Bus = validated_data['bus']
        pickup_date = validated_data['pickup_date']

        # ── Availability check ──
        if not bus.is_available_on(pickup_date):
            # Error Code: BOK-SERV-CONFLICT-001
            # Message: Bus not available on selected date
            # Cause: Another booking or manual block exists for this date
            # Solution: Choose a different date or a different bus
            raise ValidationError(
                'Bus is not available on the selected date.',
                code='BOK-SERV-CONFLICT-001',
            )

        # ── Pricing calculation ──
        pricing = BookingService._calculate_pricing(bus, validated_data)

        booking = Booking(
            customer=customer,
            operator=bus.operator,
            **{k: v for k, v in validated_data.items() if k not in ('bus',)},
            bus=bus,
            base_amount=pricing['base_amount'],
            driver_charge=pricing['driver_charge'],
            night_charge=pricing['night_charge'],
            toll_estimate=pricing['toll_estimate'],
            platform_fee=pricing['platform_fee'],
            total_amount=pricing['total_amount'],
            commission_rate=pricing['commission_rate'],
            commission_amount=pricing['commission_amount'],
            operator_payout=pricing['operator_payout'],
        )
        booking.full_clean()
        booking.save()

        # ── Block date ──
        AvailabilityBlock.objects.create(
            bus=bus,
            blocked_date=pickup_date,
            block_reason='booked_platform',
            booking=booking,
        )

        # ── History entry ──
        BookingHistory.objects.create(
            booking=booking,
            old_status='',
            new_status='pending',
            reason='Booking created',
            created_by=customer,
        )

        return booking

    @staticmethod
    def _calculate_pricing(bus: Bus, validated_data: dict) -> dict:
        """Calculate full pricing breakdown for a booking.

        Returns:
            Dict with base_amount, driver_charge, night_charge,
            toll_estimate, platform_fee, total_amount,
            commission_rate, commission_amount, operator_payout.
        """
        estimated_km = validated_data.get('estimated_km') or Decimal('0')
        base_price = bus.base_price or Decimal('0')
        distance_charge = Decimal(str(estimated_km)) * (bus.price_per_km or Decimal('0'))
        driver_charge = bus.driver_charge or Decimal('0')
        night_charge = bus.night_charge or Decimal('0')
        toll_estimate = Decimal('0')

        TWO_PLACES = Decimal('0.01')

        subtotal = base_price + distance_charge + driver_charge + night_charge + toll_estimate
        platform_fee = (subtotal * Decimal('0.05')).quantize(TWO_PLACES)

        commission_rate = (
            bus.operator.commission_rate
            if bus.operator.commission_rate is not None
            else Decimal('10')
        )
        commission_amount = (subtotal * commission_rate / 100).quantize(TWO_PLACES)
        operator_payout = (subtotal - commission_amount).quantize(TWO_PLACES)
        total_amount = (subtotal + platform_fee).quantize(TWO_PLACES)

        return {
            'base_amount': (base_price + distance_charge).quantize(TWO_PLACES),
            'driver_charge': driver_charge,
            'night_charge': night_charge,
            'toll_estimate': toll_estimate,
            'platform_fee': platform_fee,
            'total_amount': total_amount,
            'commission_rate': commission_rate,
            'commission_amount': commission_amount,
            'operator_payout': operator_payout,
        }

    @staticmethod
    @transaction.atomic
    def respond_to_booking(
        *,
        booking: Booking,
        new_status: str,
        reason: str = '',
        responded_by: CustomUser,
    ) -> Booking:
        """Operator confirms or rejects a pending booking.

        Args:
            booking: The booking to respond to.
            new_status: 'confirmed' or 'rejected'.
            reason: Optional rejection reason.
            responded_by: The operator/admin performing the action.

        Returns:
            The updated Booking instance.

        Raises:
            ValidationError: If the booking is not pending or status is invalid.
        """
        if booking.status != 'pending':
            # Error Code: BOK-SERV-VAL-001
            # Message: Booking is not in pending status
            # Cause: Operator tried to respond to a non-pending booking
            # Solution: Only pending bookings can be confirmed or rejected
            raise ValidationError(
                'Booking is not pending.',
                code='BOK-SERV-VAL-001',
            )

        old_status = booking.status

        if new_status == 'confirmed':
            booking.status = 'confirmed'
            booking.operator_response = 'accepted'
            booking.operator_response_at = timezone.now()
        elif new_status == 'rejected':
            booking.status = 'cancelled_by_operator'
            booking.operator_response = 'rejected'
            booking.operator_response_at = timezone.now()
            booking.rejection_reason = reason
            AvailabilityBlock.objects.filter(booking=booking).delete()
        else:
            # Error Code: BOK-SERV-VAL-002
            # Message: Invalid respond status
            # Cause: Status must be 'confirmed' or 'rejected'
            # Solution: Pass new_status='confirmed' or new_status='rejected'
            raise ValidationError(
                'Invalid status for respond. Use confirmed or rejected.',
                code='BOK-SERV-VAL-002',
            )

        booking.save()

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=booking.status,
            reason=reason,
            created_by=responded_by,
        )
        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(
        *,
        booking: Booking,
        reason: str = 'Cancelled by customer',
        cancelled_by: CustomUser,
    ) -> Booking:
        """Cancel a booking and free blocked dates.

        Args:
            booking: The booking to cancel.
            reason: Cancellation reason text.
            cancelled_by: The user performing the cancellation.

        Returns:
            The updated Booking instance.

        Raises:
            ValidationError: If the booking cannot be cancelled.
        """
        non_cancellable = ('completed', 'cancelled_by_customer', 'cancelled_by_operator')
        if booking.status in non_cancellable:
            # Error Code: BOK-SERV-CONFLICT-002
            # Message: Cannot cancel this booking
            # Cause: Booking is already completed or cancelled
            # Solution: Only pending or confirmed bookings can be cancelled
            raise ValidationError(
                'Cannot cancel this booking.',
                code='BOK-SERV-CONFLICT-002',
            )

        old_status = booking.status
        booking.status = 'cancelled_by_customer'
        booking.cancellation_reason = reason
        booking.cancelled_at = timezone.now()
        booking.save()

        # Free blocked dates
        AvailabilityBlock.objects.filter(booking=booking).delete()

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status='cancelled_by_customer',
            reason=reason,
            created_by=cancelled_by,
        )
        return booking

    @staticmethod
    @transaction.atomic
    def complete_booking(
        *,
        booking: Booking,
        completed_by: CustomUser,
    ) -> Booking:
        """Mark a confirmed booking as completed and update counters.

        Args:
            booking: The booking to complete.
            completed_by: The operator/admin performing the action.

        Returns:
            The updated Booking instance.

        Raises:
            ValidationError: If the booking is not confirmed.
        """
        if booking.status != 'confirmed':
            # Error Code: BOK-SERV-CONFLICT-003
            # Message: Only confirmed bookings can be completed
            # Cause: Booking status is not 'confirmed'
            # Solution: Confirm the booking first before marking complete
            raise ValidationError(
                'Only confirmed bookings can be completed.',
                code='BOK-SERV-CONFLICT-003',
            )

        old_status = booking.status
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.save()

        # Atomic increments using F() expressions to prevent race conditions
        CustomUser.objects.filter(pk=booking.customer.pk).update(
            total_bookings=F('total_bookings') + 1,
        )
        Bus.objects.filter(pk=booking.bus.pk).update(
            total_trips=F('total_trips') + 1,
        )
        CustomUser.objects.filter(pk=booking.operator.pk).update(
            total_bookings=F('total_bookings') + 1,
        )

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status='completed',
            reason='Trip completed',
            created_by=completed_by,
        )
        return booking


class PaymentService:
    """Handles payment initiation and confirmation."""

    @staticmethod
    @transaction.atomic
    def initiate_payment(
        *,
        booking: Booking,
        customer: CustomUser,
        payment_method: str = 'upi',
    ) -> Payment:
        """Create a payment record and Cashfree order for a booking.

        Args:
            booking: The booking to pay for.
            customer: The customer initiating the payment.
            payment_method: Payment method (upi, card, etc.).

        Returns:
            The newly created Payment instance with cf_order_id.

        Raises:
            ValidationError: If the booking is not owned by customer or Cashfree fails.
        """
        # Verify ownership
        if booking.customer_id != customer.id:
            # Error Code: BOK-SERV-PERM-001
            # Message: Only booking owner can pay
            # Cause: Customer ID doesn't match booking's customer
            # Solution: Ensure user is the booking owner
            raise ValidationError(
                'You can only pay for your own bookings.',
                code='BOK-SERV-PERM-001',
            )

        amount = booking.total_amount
        if booking.payment_mode == 'online_advance':
            amount = booking.advance_amount or (
                booking.total_amount * Decimal('0.3')
            ).quantize(Decimal('0.01'))

        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_type='advance' if booking.payment_mode == 'online_advance' else 'full',
            payment_method=payment_method,
        )

        # ── Create Cashfree Order ──
        cf_order_id = PaymentService._create_cashfree_order(
            payment=payment,
            customer=customer,
        )
        if cf_order_id:
            payment.cf_order_id = cf_order_id
            payment.save(update_fields=['cf_order_id'])

        return payment

    @staticmethod
    def _create_cashfree_order(
        *,
        payment: Payment,
        customer: CustomUser,
    ) -> Optional[str]:
        """Create an order on Cashfree and return the order_id.

        Args:
            payment: The Payment record to create a CF order for.
            customer: The customer making the payment.

        Returns:
            Cashfree order_id string, or None if credentials are missing.

        Raises:
            ValidationError: If Cashfree API call fails.
        """
        from django.conf import settings

        app_id = settings.CASHFREE_APP_ID
        secret_key = settings.CASHFREE_SECRET_KEY

        if not app_id or not secret_key:
            # Error Code: PAY-SERV-CONFIG-001
            # Message: Cashfree credentials missing
            # Cause: CASHFREE_APP_ID or CASHFREE_SECRET_KEY not set
            # Solution: Set credentials in .env file
            logger.warning(
                'Cashfree credentials missing — skipping order creation '
                '[PAY-SERV-CONFIG-001]'
            )
            return None

        try:
            import requests

            # Determine API base URL (TEST vs PRODUCTION)
            is_test = app_id.startswith('TEST')
            base_url = (
                'https://sandbox.cashfree.com/pg'
                if is_test
                else 'https://api.cashfree.com/pg'
            )

            headers = {
                'Content-Type': 'application/json',
                'x-client-id': app_id,
                'x-client-secret': secret_key,
                'x-api-version': settings.CASHFREE_API_VERSION,
            }

            order_data = {
                'order_id': str(payment.id),
                'order_amount': float(payment.amount),
                'order_currency': 'INR',
                'customer_details': {
                    'customer_id': str(customer.id),
                    'customer_phone': customer.phone or '',
                    'customer_name': customer.name or customer.username,
                    'customer_email': customer.email or '',
                },
                'order_meta': {
                    'return_url': f'{settings.SUPABASE_URL}/payment/return?order_id={{order_id}}',
                },
            }

            resp = requests.post(
                f'{base_url}/orders',
                json=order_data,
                headers=headers,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return data.get('cf_order_id') or data.get('order_id', '')
            else:
                # Error Code: PAY-SERV-API-001
                # Message: Cashfree API error
                # Cause: Cashfree returned non-2xx status
                # Solution: Check Cashfree dashboard and logs
                logger.error(
                    'Cashfree order creation failed: %s %s [PAY-SERV-API-001]',
                    resp.status_code,
                    resp.text,
                )
                raise ValidationError(
                    'Payment gateway error. Please try again.',
                    code='PAY-SERV-API-001',
                )
        except ValidationError:
            raise
        except Exception as e:
            # Error Code: PAY-SERV-API-001
            # Message: Cashfree API error
            # Cause: Network/connection error
            # Solution: Check connectivity and Cashfree status
            logger.error('Cashfree API call failed', exc_info=True)
            raise ValidationError(
                'Payment gateway unavailable. Please try again.',
                code='PAY-SERV-API-001',
            )

    @staticmethod
    @transaction.atomic
    def confirm_payment(
        *,
        payment: Payment,
        cf_payment_id: str = '',
        metadata: Optional[dict] = None,
        confirmed_by: CustomUser,
    ) -> Payment:
        """Confirm a payment after Cashfree callback.

        Args:
            payment: The payment to confirm.
            cf_payment_id: Cashfree payment ID.
            metadata: Additional payment metadata.
            confirmed_by: The user confirming the payment.

        Returns:
            The updated Payment instance.
        """
        payment.status = 'captured'
        payment.cf_payment_id = cf_payment_id
        payment.metadata = metadata or {}
        payment.save()

        booking = payment.booking
        old_status = booking.status

        if payment.payment_type == 'advance':
            booking.payment_status = 'advance_paid'
        else:
            # Check if total payments cover the booking amount
            from django.db.models import Sum
            total_paid = Payment.objects.filter(
                booking=booking, status='captured',
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            total_paid += payment.amount
            if total_paid >= booking.total_amount:
                booking.payment_status = 'fully_paid'
            else:
                booking.payment_status = 'advance_paid'

        if booking.status == 'pending' and booking.payment_status == 'fully_paid':
            booking.status = 'confirmed'
        booking.save()

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=booking.status,
            reason='Payment confirmed',
            created_by=confirmed_by,
        )
        return payment


class CouponService:
    """Handles coupon validation and discount calculation."""

    @staticmethod
    def validate_and_calculate(
        *,
        code: str,
        booking_amount: Decimal,
        user: CustomUser,
    ) -> dict:
        """Validate a coupon and calculate the discount.

        Args:
            code: The coupon code to validate.
            booking_amount: The booking amount to apply discount on.
            user: The user applying the coupon.

        Returns:
            Dict with coupon, discount, and final_amount.

        Raises:
            ValidationError: If the coupon is invalid, expired, or usage exceeded.
        """
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            # Error Code: BOK-SERV-VAL-003
            # Message: Invalid coupon code
            # Cause: No coupon found matching the provided code
            # Solution: Verify the coupon code and try again
            raise ValidationError(
                'Invalid coupon code.',
                code='BOK-SERV-VAL-003',
            )

        if not coupon.is_valid:
            # Error Code: BOK-SERV-VAL-004
            # Message: Coupon is expired or exhausted
            # Cause: Coupon validity period ended or usage limit reached
            # Solution: Use a different coupon code
            raise ValidationError(
                'Coupon is expired or exhausted.',
                code='BOK-SERV-VAL-004',
            )

        if coupon.min_booking and booking_amount < coupon.min_booking:
            # Error Code: BOK-SERV-VAL-005
            # Message: Booking amount below coupon minimum
            # Cause: Booking amount is less than coupon's min_booking threshold
            # Solution: Increase booking amount or use a different coupon
            raise ValidationError(
                f'Minimum booking amount is ₹{coupon.min_booking}.',
                code='BOK-SERV-VAL-005',
            )

        # Per-user limit check
        user_uses = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if coupon.per_user_limit and user_uses >= coupon.per_user_limit:
            # Error Code: BOK-SERV-VAL-006
            # Message: Coupon per-user limit reached
            # Cause: User has already used this coupon the maximum allowed times
            # Solution: Use a different coupon code
            raise ValidationError(
                'You have already used this coupon.',
                code='BOK-SERV-VAL-006',
            )

        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount = (
                booking_amount * coupon.discount_value / 100
            ).quantize(Decimal('0.01'))
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            discount = min(Decimal(str(coupon.discount_value)), booking_amount)
            discount = discount.quantize(Decimal('0.01'))

        final_amount = booking_amount - discount

        return {
            'coupon': coupon,
            'discount': discount,
            'final_amount': final_amount,
        }
