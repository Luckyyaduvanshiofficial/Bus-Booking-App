"""Business logic for bookings, payments, and coupons.

All multi-step operations use @transaction.atomic.
Raises ValidationError for invalid data.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import F, Sum
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

        Acquires a row-level lock on the bus via select_for_update() to
        prevent double-booking race conditions.

        Args:
            customer: The authenticated customer placing the booking.
            validated_data: Serializer-validated booking data.

        Returns:
            The newly created Booking instance.

        Raises:
            ValidationError (BOK-SERV-CONFLICT-001): If the bus is not
                available on the selected date.
        """
        pickup_date = validated_data['pickup_date']

        # Step 1: Acquire row-level lock on the bus to serialize concurrent bookings.
        # SELECT ... FOR UPDATE prevents other transactions from reading this row
        # until we commit, eliminating the race condition window between the
        # availability check and the AvailabilityBlock creation.
        bus: Bus = Bus.objects.select_for_update().get(
            id=validated_data['bus'].id,
        )

        # Step 2: Availability check (now safe under lock)
        # For multi-day/round-trip, check ALL dates in the range
        from datetime import timedelta
        return_date = validated_data.get('return_date')
        dates_to_check = [pickup_date]
        if return_date and return_date > pickup_date:
            current = pickup_date + timedelta(days=1)
            while current <= return_date:
                dates_to_check.append(current)
                current += timedelta(days=1)

        blocked = AvailabilityBlock.objects.filter(
            bus=bus,
            blocked_date__in=dates_to_check,
        ).values_list('blocked_date', flat=True)
        if blocked:
            blocked_str = ', '.join(str(d) for d in blocked)
            # Error Code: BOK-SERV-CONFLICT-001
            # Message: Bus not available on selected date(s)
            # Cause: Another booking or manual block exists for these dates
            # Solution: Choose different dates or a different bus
            raise ValidationError(
                f'Bus is not available on: {blocked_str}.',
                code='BOK-SERV-CONFLICT-001',
            )

        # ── Pricing calculation ──
        pricing = BookingService._calculate_pricing(bus, validated_data)

        # ── Payment mode calculation ──
        payment_mode = validated_data.get('payment_mode', 'online_full')
        total_amount = pricing['total_amount']
        
        if payment_mode == 'online_full':
            advance_amount = total_amount
            remaining_amount = Decimal('0')
        elif payment_mode == 'online_advance':
            advance_amount = min(Decimal('3000'), total_amount)
            remaining_amount = total_amount - advance_amount
        elif payment_mode == 'pay_driver':
            advance_amount = min(Decimal('500'), total_amount)
            remaining_amount = total_amount - advance_amount
        else:
            advance_amount = total_amount
            remaining_amount = Decimal('0')

        # ── Set expires_at (2 hours from now) ──
        expires_at = timezone.now() + timedelta(hours=2)

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
            total_amount=total_amount,
            commission_rate=pricing['commission_rate'],
            commission_amount=pricing['commission_amount'],
            operator_payout=pricing['operator_payout'],
            advance_amount=advance_amount,
            remaining_amount=remaining_amount,
            expires_at=expires_at,
        )
        booking.full_clean()
        booking.save()

        # ── Block dates ──
        # For round-trip or multi-day bookings, block ALL dates between
        # pickup and return to prevent double-booking on intermediate days
        if return_date and return_date > pickup_date:
            current_date = pickup_date
            while current_date <= return_date:
                _, created = AvailabilityBlock.objects.get_or_create(
                    bus=bus,
                    blocked_date=current_date,
                    defaults={
                        'block_reason': 'booked_platform',
                        'booking': booking,
                    },
                )
                if not created:
                    raise ValidationError(
                        'Bus is not available on selected date.',
                        code='BOK-SERV-CONFLICT-001',
                    )
                current_date += timedelta(days=1)
        else:
            _, created = AvailabilityBlock.objects.get_or_create(
                bus=bus,
                blocked_date=pickup_date,
                defaults={
                    'block_reason': 'booked_platform',
                    'booking': booking,
                },
            )
            if not created:
                raise ValidationError(
                    'Bus is not available on selected date.',
                    code='BOK-SERV-CONFLICT-001',
                )

        # ── History entry ──
        BookingHistory.objects.create(
            booking=booking,
            old_status='',
            new_status='pending',
            reason='Booking created',
            created_by=customer,
        )

        # ── Send notifications after commit (avoid side effects inside atomic) ──
        from apps.common.notification_service import NotificationService

        # Capture values for the on_commit closure
        _booking_number = booking.booking_number
        _bus_name = bus.name
        _pickup_location = booking.pickup_location
        _drop_location = booking.drop_location
        _pickup_date_str = booking.pickup_date.strftime("%d %b %Y")
        _total_amount = booking.total_amount
        _booking_id = str(booking.id)
        _customer = customer
        _operator = bus.operator
        _customer_name = customer.name
        _customer_phone = customer.phone

        def _send_booking_created_notifications():
            # Notify customer via WhatsApp
            NotificationService.create_notification(
                user=_customer,
                notification_type='booking_created',
                title=f'Booking Created - {_booking_number}',
                message=(
                    f'Your booking request has been created.\n\n'
                    f'📋 Booking: {_booking_number}\n'
                    f'🚍 Bus: {_bus_name}\n'
                    f'📍 Route: {_pickup_location} → {_drop_location}\n'
                    f'📅 Date: {_pickup_date_str}\n'
                    f'💰 Amount: ₹{_total_amount}\n\n'
                    f'Waiting for operator confirmation...'
                ),
                metadata={'booking_id': _booking_id},
                send_whatsapp=True,
                send_email=False
            )
            # Notify operator via WhatsApp + Email
            NotificationService.create_notification(
                user=_operator,
                notification_type='booking_created',
                title=f'New Booking Request - {_booking_number}',
                message=(
                    f'New booking request received.\n\n'
                    f'📋 Booking: {_booking_number}\n'
                    f'👤 Customer: {_customer_name}\n'
                    f'📞 Phone: {_customer_phone}\n'
                    f'📍 Route: {_pickup_location} → {_drop_location}\n'
                    f'📅 Date: {_pickup_date_str}\n'
                    f'💰 Amount: ₹{_total_amount}\n\n'
                    f'Please respond within 2 hours.'
                ),
                metadata={'booking_id': _booking_id},
                send_whatsapp=True,
                send_email=True
            )

        transaction.on_commit(_send_booking_created_notifications)

        return booking

    @staticmethod
    def _calculate_pricing(bus: Bus, validated_data: dict) -> dict:
        """Calculate full pricing breakdown for a booking.

        Uses the charter bus pricing formula from pricing.py:
            base_fare = max(base_price, price_per_km × distance)
            + driver charge × trip_days
            + night halt × (trip_days - 1)
            + toll estimate (2% of base)
            + platform fee (max ₹199, 3% of subtotal)

        Returns:
            Dict with base_amount, driver_charge, night_charge,
            toll_estimate, platform_fee, total_amount,
            commission_rate, commission_amount, operator_payout.
        """
        from apps.bookings.pricing import calculate_booking_price, calculate_trip_days

        estimated_km = validated_data.get('estimated_km') or Decimal('0')
        trip_type = validated_data.get('trip_type', 'one_way')
        pickup_date = validated_data.get('pickup_date')
        return_date = validated_data.get('return_date')

        trip_days = calculate_trip_days(pickup_date, return_date, trip_type)

        commission_rate = (
            bus.operator.commission_rate
            if bus.operator.commission_rate is not None
            else Decimal('10')
        )

        pricing = calculate_booking_price(
            distance_km=Decimal(str(estimated_km)),
            base_price=bus.base_price or Decimal('0'),
            price_per_km=bus.price_per_km or Decimal('0'),
            driver_charge_per_day=bus.driver_charge or Decimal('0'),
            night_halt_charge=bus.night_charge or Decimal('0'),
            trip_days=trip_days,
            trip_type=trip_type,
            commission_rate=commission_rate,
        )

        return {
            'base_amount': pricing['base_fare'],
            'driver_charge': pricing['driver_charge'],
            'night_charge': pricing['night_charge'],
            'toll_estimate': pricing['toll_estimate'],
            'platform_fee': pricing['platform_fee'],
            'total_amount': pricing['total'],
            'commission_rate': pricing['commission_rate'],
            'commission_amount': pricing['commission_amount'],
            'operator_payout': pricing['operator_payout'],
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
        booking = Booking.objects.select_for_update().get(pk=booking.pk)

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
            booking.rejection_reason = ''
            booking.cancelled_at = None
            update_fields = [
                'status',
                'operator_response',
                'operator_response_at',
                'rejection_reason',
                'cancelled_at',
            ]
        elif new_status == 'rejected':
            booking.status = 'cancelled_by_operator'
            booking.operator_response = 'rejected'
            booking.operator_response_at = timezone.now()
            booking.rejection_reason = reason
            booking.cancelled_at = timezone.now()
            update_fields = [
                'status',
                'operator_response',
                'operator_response_at',
                'rejection_reason',
                'cancelled_at',
            ]
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

        booking.save(update_fields=update_fields)

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=booking.status,
            reason=reason,
            created_by=responded_by,
        )
        
        # ── Send notifications after commit ──
        from apps.common.notification_service import NotificationService

        # Capture values for closure
        _booking_number = booking.booking_number
        _bus_name = booking.bus.name
        _customer = booking.customer
        _pickup_date_str = booking.pickup_date.strftime("%d %b %Y")
        _booking_id = str(booking.id)
        _total_amount = booking.total_amount
        _advance_amount = booking.advance_amount
        _remaining_amount = booking.remaining_amount
        _operator_name = booking.operator.business_name or booking.operator.name
        _operator_phone = booking.operator.phone
        _pickup_location = booking.pickup_location
        _pickup_time_str = booking.pickup_time.strftime("%I:%M %p")

        if new_status == 'confirmed':
            def _send_confirmed_notification():
                NotificationService.create_notification(
                    user=_customer,
                    notification_type='booking_confirmed',
                    title=f'✅ Booking Confirmed - {_booking_number}',
                    message=(
                        f'Great news! Your booking has been confirmed.\n\n'
                        f'📋 Booking: {_booking_number}\n'
                        f'🚍 Bus: {_bus_name}\n'
                        f'👤 Operator: {_operator_name}\n'
                        f'📞 Contact: {_operator_phone}\n'
                        f'📍 Pickup: {_pickup_location}\n'
                        f'📅 Date: {_pickup_date_str}\n'
                        f'🕒 Time: {_pickup_time_str}\n'
                        f'💰 Total: ₹{_total_amount}\n'
                        f'💳 Paid: ₹{_advance_amount}\n'
                        f'💵 Remaining: ₹{_remaining_amount}\n\n'
                        f'We will send you a reminder before your trip. Have a safe journey!'
                    ),
                    metadata={'booking_id': _booking_id},
                    send_whatsapp=True,
                    send_email=True
                )
            transaction.on_commit(_send_confirmed_notification)
        elif new_status == 'rejected':
            _rejection_reason = reason or 'No reason provided'
            def _send_rejected_notification():
                NotificationService.create_notification(
                    user=_customer,
                    notification_type='booking_rejected',
                    title=f'❌ Booking Rejected - {_booking_number}',
                    message=(
                        f'Unfortunately, your booking request has been rejected.\n\n'
                        f'📋 Booking: {_booking_number}\n'
                        f'🚍 Bus: {_bus_name}\n'
                        f'📅 Date: {_pickup_date_str}\n\n'
                        f'Reason: {_rejection_reason}\n\n'
                        f'We apologize for the inconvenience. Please try booking another bus or contact us for assistance.'
                    ),
                    metadata={
                        'booking_id': _booking_id,
                        'rejection_reason': _rejection_reason
                    },
                    send_whatsapp=True,
                    send_email=True
                )
            transaction.on_commit(_send_rejected_notification)
        
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

        Sets the correct cancellation status based on who cancelled:
        - Customer → cancelled_by_customer
        - Operator → cancelled_by_operator
        - Admin → cancelled_by_operator (administrative cancellation)

        Args:
            booking: The booking to cancel.
            reason: Cancellation reason text.
            cancelled_by: The user performing the cancellation.

        Returns:
            The updated Booking instance.

        Raises:
            ValidationError (BOK-SERV-CONFLICT-002): If the booking cannot be cancelled.
        """
        booking = Booking.objects.select_for_update().get(pk=booking.pk)

        # Use state machine guard
        if not booking.can_cancel():
            # Error Code: BOK-SERV-CONFLICT-002
            # Message: Cannot cancel this booking
            # Cause: Booking is already completed or cancelled
            # Solution: Only pending or confirmed bookings can be cancelled
            logger.warning(
                'booking_cancel_attempt_invalid_state',
                extra={
                    'error_code': 'BOK-SERV-CONFLICT-002',
                    'booking_id': str(booking.id),
                    'booking_number': booking.booking_number,
                    'current_status': booking.status,
                    'cancelled_by_id': str(cancelled_by.id),
                },
            )
            raise ValidationError(
                'Cannot cancel this booking.',
                code='BOK-SERV-CONFLICT-002',
            )

        old_status = booking.status
        normalized_reason = (reason or '').strip()
        if not normalized_reason:
            if cancelled_by.role in (
                CustomUser.Role.OPERATOR,
                CustomUser.Role.ADMIN,
            ):
                raise ValidationError(
                    'Cancellation reason is required for operators/admins.',
                    code='BOK-SERV-VAL-007',
                )
            normalized_reason = 'Cancelled by customer'

        # Determine correct cancellation status based on who is cancelling
        if cancelled_by.role in (
            CustomUser.Role.OPERATOR,
            CustomUser.Role.ADMIN,
        ):
            new_status = Booking.Status.CANCELLED_BY_OPERATOR
        else:
            new_status = Booking.Status.CANCELLED_BY_CUSTOMER

        # Calculate refund eligibility
        captured_total = Payment.objects.filter(
            booking=booking,
            status=Payment.CfStatus.CAPTURED,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        refund_amount = Decimal('0.00')
        if captured_total > 0:
            refund_amount = min(
                booking.calculate_refund(),
                captured_total,
            ).quantize(Decimal('0.01'))

        # Phase 1: Mark refund intent (inside DB transaction)
        if refund_amount > 0:
            booking.payment_status = Booking.PaymentStatus.REFUND_PENDING
            logger.info(
                'booking_refund_marked_pending',
                extra={
                    'booking_id': str(booking.id),
                    'booking_number': booking.booking_number,
                    'refund_amount': str(refund_amount),
                    'captured_total': str(captured_total),
                },
            )
        
        # Use state machine transition
        booking.transition_to(new_status)
        booking.cancellation_reason = normalized_reason
        booking.cancelled_at = timezone.now()
        booking.refund_amount = refund_amount
        update_fields = [
            'status',
            'cancellation_reason',
            'cancelled_at',
            'refund_amount',
            'payment_status',
        ]
        booking.save(update_fields=update_fields)

        # Free blocked dates
        AvailabilityBlock.objects.filter(booking=booking).delete()

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=new_status,
            reason=normalized_reason,
            created_by=cancelled_by,
        )
        
        logger.info(
            'booking_cancelled',
            extra={
                'booking_id': str(booking.id),
                'booking_number': booking.booking_number,
                'old_status': old_status,
                'new_status': new_status,
                'cancelled_by_id': str(cancelled_by.id),
                'refund_amount': str(refund_amount),
            },
        )
        
        # Phase 2: Schedule refund processing (outside DB lock)
        if refund_amount > 0:
            PaymentService.schedule_booking_refund_post_commit(
                booking_id=booking.id,
                amount=refund_amount,
                reason=normalized_reason,
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
        booking = Booking.objects.select_for_update().select_related(
            'customer', 'operator', 'bus',
        ).get(pk=booking.pk)

        old_status = booking.status
        completed_at = timezone.now()
        
        # Use state machine transition
        booking.transition_to(Booking.Status.COMPLETED)
        booking.completed_at = completed_at
        booking.save(update_fields=['status', 'completed_at'])
        
        logger.info(
            'booking_completed',
            extra={
                'booking_id': str(booking.id),
                'booking_number': booking.booking_number,
                'old_status': old_status,
                'completed_by_id': str(completed_by.id),
                'operator_id': str(booking.operator.id),
            },
        )

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

        Returns an existing pending payment if one already exists
        (idempotency guard to prevent duplicate Cashfree orders).

        Args:
            booking: The booking to pay for.
            customer: The customer initiating the payment.
            payment_method: Payment method (upi, card, etc.).

        Returns:
            The newly created (or existing pending) Payment instance.

        Raises:
            ValidationError (BOK-SERV-PERM-001): If the booking is not
                owned by customer.
            ValidationError (PAY-SERV-API-001): If Cashfree order
                creation fails.
        """
        booking = Booking.objects.select_for_update().get(pk=booking.pk)

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

        payment_type = 'advance' if booking.payment_mode == 'online_advance' else 'full'

        # Idempotency guard — return existing pending payment instead of
        # creating a duplicate Cashfree order when user clicks "Pay" twice
        existing_pending = Payment.objects.filter(
            booking=booking,
            status='created',
            payment_type=payment_type,
        ).first()
        if existing_pending:
            return existing_pending

        amount = booking.total_amount
        if booking.payment_mode == 'online_advance':
            amount = booking.advance_amount or (
                booking.total_amount * Decimal('0.3')
            ).quantize(Decimal('0.01'))

        # Generate idempotency key to prevent duplicate payments
        idempotency_key = f"booking-{booking.id}-{payment_type}"
        
        logger.info(
            'payment_initiation_started',
            extra={
                'booking_id': str(booking.id),
                'booking_number': booking.booking_number,
                'payment_type': payment_type,
                'amount': str(amount),
                'idempotency_key': idempotency_key,
            },
        )

        try:
            payment = Payment.objects.create(
                booking=booking,
                amount=amount,
                payment_type=payment_type,
                payment_method=payment_method,
                idempotency_key=idempotency_key,
            )
        except IntegrityError:
            # Idempotency key or unique constraint violation
            existing_pending = Payment.objects.filter(
                booking=booking,
                status='created',
                payment_type=payment_type,
            ).first()
            if existing_pending:
                logger.info(
                    'payment_already_exists',
                    extra={
                        'booking_id': str(booking.id),
                        'payment_id': str(existing_pending.id),
                        'idempotency_key': idempotency_key,
                    },
                )
                return existing_pending
            raise ValidationError(
                'Race condition detected. Please retry.',
                code='BOK-SERV-DB-002',
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
            from requests import RequestException

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
                    'return_url': (
                        f"{(getattr(settings, 'FRONTEND_URL', '') or getattr(settings, 'SUPABASE_URL', '')).rstrip('/')}"
                        "/payment/return?order_id={order_id}"
                    ),
                },
            }

            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = requests.post(
                        f'{base_url}/orders',
                        json=order_data,
                        headers=headers,
                        timeout=30,
                    )
                except RequestException:
                    if attempt == max_attempts:
                        raise
                    time.sleep(2 ** (attempt - 1))
                    continue

                if resp.status_code in (200, 201):
                    data = resp.json()
                    return data.get('cf_order_id') or data.get('order_id', '')

                # Retry only transient server errors
                if resp.status_code >= 500 and attempt < max_attempts:
                    time.sleep(2 ** (attempt - 1))
                    continue

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
        except Exception:
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
    def create_refund_record(
        *,
        booking: Booking,
        source_payment: Payment,
        amount: Decimal,
        reason: str = '',
    ) -> Payment:
        """Create refund payment and attempt gateway refund using two-phase commit.
        
        Phase 1: Create REFUND_PENDING record in DB (inside transaction)
        Phase 2: Call external gateway API (outside transaction lock)
        Phase 3: Update to REFUNDED or REFUND_FAILED based on gateway response
        """
        normalized_amount = amount.quantize(Decimal('0.01'))
        existing_refund = PaymentService._find_existing_refund_for_source_payment(
            booking=booking,
            source_payment=source_payment,
            amount=normalized_amount,
        )
        if existing_refund:
            logger.info(
                'refund_already_exists',
                extra={
                    'booking_id': str(booking.id),
                    'refund_payment_id': str(existing_refund.id),
                    'amount': str(normalized_amount),
                },
            )
            return existing_refund

        # Phase 1: Create refund record with REFUND_PENDING status (inside DB lock)
        refund_payment = Payment.objects.create(
            booking=booking,
            amount=normalized_amount,
            payment_type=Payment.PaymentType.REFUND,
            payment_method=source_payment.payment_method,
            status=Payment.CfStatus.REFUND_PENDING,  # Two-phase: mark intent first
            metadata={
                'source_payment_id': str(source_payment.id),
                'refund_reason': reason,
            },
        )
        
        logger.info(
            'refund_marked_pending',
            extra={
                'booking_id': str(booking.id),
                'refund_payment_id': str(refund_payment.id),
                'source_payment_id': str(source_payment.id),
                'amount': str(normalized_amount),
            },
        )

        # Phase 2: Call external gateway API (now outside DB transaction lock)
        # This prevents holding DB locks during network I/O
        gateway_result = PaymentService._create_cashfree_refund(
            source_payment=source_payment,
            refund_payment=refund_payment,
            refund_amount=normalized_amount,
            reason=reason,
        )
        
        # Phase 3: Update final status based on gateway response
        refund_payment.metadata = {
            **(refund_payment.metadata or {}),
            'gateway_refund': gateway_result,
        }
        if gateway_result.get('success'):
            refund_payment.status = Payment.CfStatus.REFUNDED
            logger.info(
                'refund_gateway_success',
                extra={
                    'booking_id': str(booking.id),
                    'refund_payment_id': str(refund_payment.id),
                    'amount': str(normalized_amount),
                },
            )
        else:
            refund_payment.status = Payment.CfStatus.REFUND_FAILED
            logger.error(
                'refund_gateway_failed',
                extra={
                    'error_code': 'PAY-SERV-API-001',
                    'booking_id': str(booking.id),
                    'refund_payment_id': str(refund_payment.id),
                    'amount': str(normalized_amount),
                    'gateway_result': gateway_result,
                },
            )
        refund_payment.save(update_fields=['status', 'metadata'])
        return refund_payment

    @staticmethod
    def schedule_booking_refund_post_commit(
        *,
        booking_id,
        amount: Decimal,
        reason: str = '',
    ) -> None:
        """Process booking refund only after surrounding DB transaction commits."""
        normalized_amount = amount.quantize(Decimal('0.01'))
        if normalized_amount <= Decimal('0.00'):
            return

        def _refund_after_commit() -> None:
            try:
                booking = Booking.objects.get(pk=booking_id)
                refunded_total = PaymentService.process_booking_refund(
                    booking=booking,
                    amount=normalized_amount,
                    reason=reason,
                )
                if (
                    refunded_total >= normalized_amount
                    and booking.payment_status != Booking.PaymentStatus.REFUNDED
                ):
                    booking.payment_status = Booking.PaymentStatus.REFUNDED
                    booking.save(update_fields=['payment_status'])
            except Booking.DoesNotExist:
                logger.warning(
                    'Skipped post-commit refund; booking %s no longer exists.',
                    booking_id,
                )
            except Exception:
                logger.exception(
                    'Post-commit refund processing failed for booking %s.',
                    booking_id,
                )
                # Do NOT re-raise inside on_commit callback — Django's
                # signal dispatcher silently swallows it, and it can mask
                # the real error in logs.

        transaction.on_commit(_refund_after_commit)

    @staticmethod
    def process_booking_refund(
        *,
        booking: Booking,
        amount: Decimal,
        reason: str = '',
    ) -> Decimal:
        """Refund a booking across captured payments and return total refunded."""
        remaining = amount.quantize(Decimal('0.01'))
        if remaining <= Decimal('0.00'):
            return Decimal('0.00')

        refunded_total = Decimal('0.00')
        captured_payments = Payment.objects.filter(
            booking=booking,
            status=Payment.CfStatus.CAPTURED,
        ).order_by('-created_at', '-id')

        for source_payment in captured_payments:
            if remaining <= Decimal('0.00'):
                break

            already_refunded = PaymentService._refunded_amount_for_source_payment(
                booking=booking,
                source_payment=source_payment,
            )
            refundable_balance = (
                source_payment.amount - already_refunded
            ).quantize(Decimal('0.01'))
            if refundable_balance <= Decimal('0.00'):
                continue

            refund_chunk = min(remaining, refundable_balance).quantize(Decimal('0.01'))
            if refund_chunk <= Decimal('0.00'):
                continue

            refund_payment = PaymentService.create_refund_record(
                booking=booking,
                source_payment=source_payment,
                amount=refund_chunk,
                reason=reason,
            )
            if refund_payment.status == Payment.CfStatus.REFUNDED:
                refunded_total += refund_payment.amount
                remaining = (remaining - refund_payment.amount).quantize(Decimal('0.01'))

        return refunded_total.quantize(Decimal('0.01'))

    @staticmethod
    def _find_existing_refund_for_source_payment(
        *,
        booking: Booking,
        source_payment: Payment,
        amount: Decimal,
    ) -> Optional[Payment]:
        """Return existing non-failed refund for the same source payment + amount."""
        source_payment_id = str(source_payment.id)
        target_amount = amount.quantize(Decimal('0.01'))

        candidate_refunds = Payment.objects.filter(
            booking=booking,
            payment_type=Payment.PaymentType.REFUND,
        ).exclude(
            status=Payment.CfStatus.FAILED,
        ).only(
            'id', 'amount', 'metadata', 'status', 'created_at',
        ).order_by('-created_at')

        for refund in candidate_refunds:
            metadata = refund.metadata or {}
            if str(metadata.get('source_payment_id') or '') != source_payment_id:
                continue
            if refund.amount == target_amount:
                return refund
        return None

    @staticmethod
    def _refunded_amount_for_source_payment(
        *,
        booking: Booking,
        source_payment: Payment,
    ) -> Decimal:
        """Return total successfully refunded amount for one captured source payment."""
        source_payment_id = str(source_payment.id)
        refunded_total = Decimal('0.00')

        refund_rows = Payment.objects.filter(
            booking=booking,
            payment_type=Payment.PaymentType.REFUND,
            status=Payment.CfStatus.REFUNDED,
        ).only('amount', 'metadata')

        for refund in refund_rows:
            metadata = refund.metadata or {}
            if str(metadata.get('source_payment_id') or '') != source_payment_id:
                continue
            refunded_total += refund.amount

        return refunded_total.quantize(Decimal('0.01'))

    @staticmethod
    def _create_cashfree_refund(
        *,
        source_payment: Payment,
        refund_payment: Payment,
        refund_amount: Decimal,
        reason: str = '',
    ) -> dict:
        """Call Cashfree refund API for a captured payment."""
        from django.conf import settings

        app_id = settings.CASHFREE_APP_ID
        secret_key = settings.CASHFREE_SECRET_KEY
        if not app_id or not secret_key:
            return {'success': False, 'reason': 'credentials_missing'}

        order_id = source_payment.cf_order_id or str(source_payment.id)
        if not order_id:
            return {'success': False, 'reason': 'missing_order_id'}

        try:
            import requests
            from requests import RequestException
        except Exception:
            logger.exception('Failed to import requests for refund call')
            return {'success': False, 'reason': 'requests_import_failed'}

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
        payload = {
            'refund_id': str(refund_payment.id),
            'refund_amount': float(refund_amount),
            'refund_note': (reason or 'Booking cancellation refund')[:120],
        }

        try:
            response = requests.post(
                f'{base_url}/orders/{order_id}/refunds',
                json=payload,
                headers=headers,
                timeout=30,
            )
        except RequestException as exc:
            logger.error('Cashfree refund API call failed', exc_info=True)
            return {
                'success': False,
                'reason': 'request_failed',
                'error': str(exc),
            }

        if response.status_code in (200, 201, 202):
            try:
                data = response.json()
            except ValueError:
                data = {}
            return {
                'success': True,
                'status_code': response.status_code,
                'response': data,
            }

        logger.error(
            'Cashfree refund failed: %s %s [PAY-SERV-API-001]',
            response.status_code,
            response.text,
        )
        return {
            'success': False,
            'reason': 'gateway_error',
            'status_code': response.status_code,
            'response_text': response.text[:500],
        }

    @staticmethod
    def verify_cashfree_payment_reference(
        *,
        payment: Payment,
        cf_payment_id: str,
        expected_amount: Decimal,
    ) -> dict:
        """Verify payment reference against Cashfree order payments API."""
        from django.conf import settings
        import requests

        app_id = settings.CASHFREE_APP_ID
        secret_key = settings.CASHFREE_SECRET_KEY
        if not app_id or not secret_key:
            raise ValidationError(
                'Cashfree credentials missing for payment verification.',
                code='PAY-SERV-CONFIG-001',
            )

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
        order_id = payment.cf_order_id or str(payment.id)
        response = requests.get(
            f'{base_url}/orders/{order_id}/payments',
            headers=headers,
            timeout=30,
        )
        if response.status_code != 200:
            logger.error(
                'Cashfree verification failed: %s %s [PAY-SERV-API-001]',
                response.status_code,
                response.text,
            )
            raise ValidationError(
                'Unable to verify payment reference with gateway.',
                code='PAY-SERV-API-001',
            )

        try:
            payload = response.json()
        except ValueError:
            raise ValidationError(
                'Gateway verification returned invalid payload.',
                code='PAY-SERV-API-001',
            )
        if isinstance(payload, list):
            payment_rows = payload
        elif isinstance(payload, dict):
            payment_rows = payload.get('data') or payload.get('payments') or []
        else:
            payment_rows = []

        matched = None
        for row in payment_rows:
            row_payment_id = str(
                row.get('cf_payment_id')
                or row.get('payment_id')
                or '',
            )
            if row_payment_id == str(cf_payment_id):
                matched = row
                break

        if not matched:
            raise ValidationError(
                'Provided payment reference was not found in gateway records.',
                code='PAY-SERV-VAL-003',
            )

        gateway_amount = Decimal(
            str(
                matched.get('payment_amount')
                or matched.get('amount')
                or '0',
            ),
        )
        if abs(gateway_amount - expected_amount) > Decimal('0.01'):
            raise ValidationError(
                'Gateway amount does not match expected amount.',
                code='PAY-SERV-VAL-001',
            )

        gateway_status = str(
            matched.get('payment_status')
            or matched.get('status')
            or '',
        ).lower()
        if gateway_status not in {'success', 'captured', 'paid'}:
            raise ValidationError(
                'Gateway payment is not in captured/success state.',
                code='PAY-SERV-CONFLICT-003',
            )

        return matched

    @staticmethod
    @transaction.atomic
    def confirm_payment(
        *,
        payment: Payment,
        cf_payment_id: str = '',
        actual_amount: Optional[Decimal] = None,
        metadata: Optional[dict] = None,
        confirmed_by: Optional[CustomUser] = None,
    ) -> Payment:
        """Confirm a payment after Cashfree webhook callback.

        Verifies the actual paid amount matches the expected amount
        before marking the payment as captured.

        Args:
            payment: The payment to confirm.
            cf_payment_id: Cashfree payment ID from webhook.
            actual_amount: Actual amount received (from Cashfree webhook).
                If provided, must match payment.amount.
            metadata: Additional payment metadata from Cashfree.
            confirmed_by: The user/system confirming the payment (None for webhooks).

        Returns:
            The updated Payment instance.

        Raises:
            ValidationError (PAY-SERV-VAL-001): If actual_amount does not
                match expected payment.amount.
            ValidationError (PAY-SERV-CONFLICT-002): If payment is already
                captured (idempotency guard).
        """
        # Idempotency guard — skip if already captured
        payment = Payment.objects.select_for_update().select_related('booking').get(pk=payment.pk)

        if payment.status == 'captured':
            # Error Code: PAY-SERV-CONFLICT-002
            # Message: Payment already captured
            # Cause: Duplicate webhook or confirm call
            # Solution: No action needed — payment is already processed
            logger.info(
                'Payment %s already captured — skipping [PAY-SERV-CONFLICT-002]',
                payment.id,
            )
            return payment

        # Verify actual amount matches expected amount (prevents underpayment fraud)
        if (
            actual_amount is not None
            and abs(payment.amount - actual_amount) > Decimal('0.01')
        ):
            # Error Code: PAY-SERV-VAL-001
            # Message: Payment amount mismatch
            # Cause: Actual paid amount differs from expected booking amount
            # Solution: Investigate in Cashfree dashboard — possible fraud
            logger.error(
                'Payment amount mismatch: expected=%s actual=%s [PAY-SERV-VAL-001]',
                payment.amount,
                actual_amount,
            )
            payment.status = 'failed'
            payment.metadata = metadata or {}
            payment.save(update_fields=['status', 'metadata'])
            raise ValidationError(
                'Payment amount mismatch.',
                code='PAY-SERV-VAL-001',
            )

        payment.status = 'captured'
        payment.cf_payment_id = cf_payment_id
        payment.metadata = metadata or {}
        payment.save(update_fields=['status', 'cf_payment_id', 'metadata'])

        booking = Booking.objects.select_for_update().get(pk=payment.booking_id)
        old_status = booking.status

        # Calculate total paid — current payment is already captured and
        # included in the query result, so do NOT add it again.
        total_paid = Payment.objects.filter(
            booking=booking, status='captured',
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Update booking payment status only — do NOT auto-confirm booking.
        # Operator must explicitly confirm via the respond endpoint.
        # Auto-confirming on payment bypasses operator approval flow.
        if payment.payment_type == 'advance':
            booking.payment_status = 'advance_paid'
        elif total_paid >= booking.total_amount:
            booking.payment_status = 'fully_paid'
        else:
            booking.payment_status = 'advance_paid'

        booking.save(update_fields=['payment_status'])

        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=booking.status,
            reason='Payment confirmed',
            created_by=confirmed_by,
        )
        
        # ── Send payment received notification after commit ──
        from apps.common.notification_service import NotificationService

        # Capture values for the closure — use computed remaining instead of
        # booking.remaining_amount which may be stale after the update above.
        _remaining = booking.total_amount - total_paid
        _booking_number = booking.booking_number
        _customer = booking.customer
        _payment_amount = payment.amount
        _cf_payment_id = cf_payment_id
        _total_paid = total_paid
        _total_amount = booking.total_amount
        _booking_id = str(booking.id)
        _payment_id = str(payment.id)

        def _send_payment_notification():
            NotificationService.create_notification(
                user=_customer,
                notification_type='payment_received',
                title=f'💳 Payment Received - {_booking_number}',
                message=(
                    f'We have received your payment successfully.\n\n'
                    f'📋 Booking: {_booking_number}\n'
                    f'💰 Amount Paid: ₹{_payment_amount}\n'
                    f'💳 Payment ID: {_cf_payment_id}\n'
                    f'📅 Date: {timezone.now().strftime("%d %b %Y, %I:%M %p")}\n\n'
                    f'Total Paid: ₹{_total_paid}\n'
                    f'Total Amount: ₹{_total_amount}\n'
                    f'Remaining: ₹{_remaining}\n\n'
                    f'Thank you for your payment!'
                ),
                metadata={
                    'booking_id': _booking_id,
                    'payment_id': _payment_id,
                    'amount': str(_payment_amount)
                },
                send_sms=False,
                send_email=True
            )
        transaction.on_commit(_send_payment_notification)

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

    @staticmethod
    @transaction.atomic
    def apply_to_booking(
        *,
        coupon: Coupon,
        booking: Booking,
        user: CustomUser,
        discount: Decimal,
    ) -> CouponUsage:
        """Record coupon usage and increment the used_count.

        Call this method inside create_booking after the Booking is saved.

        Args:
            coupon: The coupon being applied.
            booking: The booking to apply the coupon to.
            user: The customer using the coupon.
            discount: The calculated discount amount.

        Returns:
            The created CouponUsage record.
        """
        coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)

        if not coupon.is_valid:
            raise ValidationError(
                'Coupon is expired or exhausted.',
                code='BOK-SERV-VAL-004',
            )

        user_uses = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if coupon.per_user_limit and user_uses >= coupon.per_user_limit:
            raise ValidationError(
                'You have already used this coupon.',
                code='BOK-SERV-VAL-006',
            )

        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            raise ValidationError(
                'Coupon is expired or exhausted.',
                code='BOK-SERV-VAL-004',
            )

        # Error Code: BOK-SERV-DB-003
        # Message: Failed to record coupon usage
        # Cause: Database constraint violation when recording coupon usage
        # Solution: Check CouponUsage unique_together constraint
        usage = CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            booking=booking,
            discount_applied=discount,
        )
        # Atomically increment used_count to avoid race conditions
        Coupon.objects.filter(id=coupon.id).update(used_count=F('used_count') + 1)
        return usage
