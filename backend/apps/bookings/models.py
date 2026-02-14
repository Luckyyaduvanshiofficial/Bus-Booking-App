"""Booking models – PRD Section 4.

Booking, Payment, BookingHistory, Coupon, and CouponUsage models.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone


class Booking(models.Model):
    """Booking model – PRD Section 4 (bookings table)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED_BY_CUSTOMER = 'cancelled_by_customer', 'Cancelled by Customer'
        CANCELLED_BY_OPERATOR = 'cancelled_by_operator', 'Cancelled by Operator'
        EXPIRED = 'expired', 'Expired'

    class TripType(models.TextChoices):
        ONE_WAY = 'one_way', 'One Way'
        ROUND_TRIP = 'round_trip', 'Round Trip'
        MULTI_DAY = 'multi_day', 'Multi Day'

    class Purpose(models.TextChoices):
        WEDDING = 'wedding', 'Wedding'
        RELIGIOUS = 'religious', 'Religious Trip'
        FAMILY_TRIP = 'family_trip', 'Family Trip'
        CORPORATE = 'corporate', 'Corporate'
        SCHOOL_TOUR = 'school_tour', 'School Tour'
        OTHER = 'other', 'Other'

    class PaymentMode(models.TextChoices):
        ONLINE_FULL = 'online_full', 'Pay Full Online'
        ONLINE_ADVANCE = 'online_advance', 'Pay Advance Online'
        PAY_DRIVER = 'pay_driver', 'Pay Driver (Cash)'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ADVANCE_PAID = 'advance_paid', 'Advance Paid'
        FULLY_PAID = 'fully_paid', 'Fully Paid'
        REFUNDED = 'refunded', 'Refunded'

    class OperatorResponse(models.TextChoices):
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    class PayoutStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSED = 'processed', 'Processed'
        PAID = 'paid', 'Paid'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    booking_number: str = models.CharField(max_length=20, unique=True, editable=False)

    # ── Parties ──
    customer: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='customer_bookings',
    )
    operator: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='operator_bookings',
    )
    bus: 'Bus' = models.ForeignKey(
        'buses.Bus', on_delete=models.CASCADE,
        related_name='bookings',
    )

    # ── Trip details ──
    trip_type: str = models.CharField(max_length=20, choices=TripType.choices)
    pickup_location: str = models.TextField()
    pickup_lat: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
    )
    pickup_lng: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
    )
    drop_location: str = models.TextField()
    drop_lat: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
    )
    drop_lng: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
    )
    pickup_date: date = models.DateField()
    pickup_time: models.TimeField = models.TimeField()
    return_date: date = models.DateField(null=True, blank=True)
    passenger_count: int = models.IntegerField()
    purpose: str = models.CharField(
        max_length=50, choices=Purpose.choices, blank=True, null=True,
    )
    special_requests: str = models.TextField(blank=True, null=True)

    # ── Distance & route ──
    estimated_km: models.DecimalField = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    estimated_route: str = models.TextField(blank=True, null=True)

    # ── Pricing breakdown ──
    base_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2,
    )
    driver_charge: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    night_charge: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    toll_estimate: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    platform_fee: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    discount_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    total_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2,
    )

    # ── Commission ──
    commission_rate: models.DecimalField = models.DecimalField(
        max_digits=4, decimal_places=2, default=10.00,
    )
    commission_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    operator_payout: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )

    # ── Status ──
    status: str = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDING,
    )

    # ── Operator response ──
    operator_response: str = models.CharField(
        max_length=20, choices=OperatorResponse.choices, blank=True, null=True,
    )
    operator_response_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True,
    )
    rejection_reason: str = models.TextField(blank=True, null=True)

    # ── Payment ──
    payment_mode: str = models.CharField(
        max_length=20, choices=PaymentMode.choices, default=PaymentMode.ONLINE_FULL,
    )
    payment_status: str = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING,
    )
    advance_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )

    # ── Cancellation ──
    cancelled_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    cancellation_reason: str = models.TextField(blank=True, null=True)
    refund_amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )

    # ── Completion ──
    completed_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    operator_payout_status: str = models.CharField(
        max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING,
    )
    operator_payout_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)

    # ── Meta ──
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['operator']),
            models.Index(fields=['bus']),
            models.Index(fields=['pickup_date']),
            models.Index(fields=['status']),
            models.Index(fields=['booking_number']),
        ]

    def __str__(self) -> str:
        return f"Booking {self.booking_number} – {self.customer}"

    def clean(self) -> None:
        """Model-level validation with error codes from ERROR_REGISTRY.md.

        Note: pickup_date past-date check only runs on creation (no pk yet).
        This prevents save() from failing when updating status on bookings
        whose trip date has already passed (e.g., marking as completed).
        """
        super().clean()
        from django.core.exceptions import ValidationError
        from datetime import date as _date

        # Error Code: BOK-MODELS-VAL-001
        # Message: Pickup datetime must be in future
        # Cause: Past date selected
        # Solution: Choose future date
        # Only validate on creation — existing bookings may have past dates
        if not self.pk and self.pickup_date and self.pickup_date < _date.today():
            raise ValidationError(
                'Pickup date must be in the future.',
                code='BOK-MODELS-VAL-001',
            )

        # Error Code: BOK-MODELS-VAL-002
        # Message: Return date must be after pickup date
        # Cause: Invalid date range
        # Solution: Fix date order
        if self.return_date and self.pickup_date and self.return_date < self.pickup_date:
            raise ValidationError(
                'Return date must be after pickup date.',
                code='BOK-MODELS-VAL-002',
            )

        # Error Code: BOK-MODELS-VAL-004
        # Message: Total amount must be positive
        # Cause: Invalid pricing calculation
        # Solution: Check pricing logic
        if self.total_amount is not None and self.total_amount <= 0:
            raise ValidationError(
                'Total amount must be positive.',
                code='BOK-MODELS-VAL-004',
            )

        # Error Code: BOK-MODELS-VAL-003
        # Message: Passenger count exceeds bus capacity
        # Cause: Too many passengers
        # Solution: Choose bigger bus or reduce passengers
        if (self.bus_id and self.passenger_count
                and hasattr(self, 'bus') and self.bus
                and self.passenger_count > self.bus.seating_capacity):
            raise ValidationError(
                f'Passenger count ({self.passenger_count}) exceeds '
                f'bus capacity ({self.bus.seating_capacity}).',
                code='BOK-MODELS-VAL-003',
            )

    def save(self, *args, **kwargs) -> None:
        """Generate booking number with random suffix and save.

        Note: full_clean() is called in BookingService.create_booking()
        before save(), so we do NOT call self.clean() here to avoid
        double validation and extra DB queries.
        """
        if not self.booking_number:
            import secrets
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    with transaction.atomic():
                        today = date.today().strftime('%Y%m%d')
                        # Use random 6-char hex suffix instead of count-based
                        # to eliminate race conditions between concurrent inserts
                        suffix = secrets.token_hex(3).upper()
                        self.booking_number = f"BK-{today}-{suffix}"
                        super().save(*args, **kwargs)
                    return
                except IntegrityError:
                    if attempt == max_attempts - 1:
                        raise
                    self.booking_number = ''
                    continue
        else:
            super().save(*args, **kwargs)

    # ── Business methods ──

    def can_cancel(self) -> bool:
        """Check if this booking can be cancelled."""
        non_cancellable = (
            self.Status.COMPLETED,
            self.Status.CANCELLED_BY_CUSTOMER,
            self.Status.CANCELLED_BY_OPERATOR,
        )
        return self.status not in non_cancellable

    def calculate_refund(self) -> Decimal:
        """Calculate refund amount based on cancellation timing.

        Returns:
            Refund amount (full refund if >48h before pickup, 50% otherwise).
        """
        if self.pickup_date is None:
            return Decimal('0')
        from datetime import datetime as _dt, time
        pickup_time = self.pickup_time or time.min
        naive_dt = _dt.combine(self.pickup_date, pickup_time)
        pickup_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
        hours_until = (pickup_dt - timezone.now()).total_seconds() / 3600
        if hours_until >= 48:
            return self.total_amount
        if hours_until >= 24:
            return (self.total_amount * Decimal('0.5')).quantize(Decimal('0.01'))
        return Decimal('0.00')


class Payment(models.Model):
    """Payment record (Cashfree) – PRD Section 4 (payments table)."""

    class PaymentType(models.TextChoices):
        ADVANCE = 'advance', 'Advance'
        FULL = 'full', 'Full Payment'
        REMAINING = 'remaining', 'Remaining Balance'
        REFUND = 'refund', 'Refund'

    class PaymentMethod(models.TextChoices):
        UPI = 'upi', 'UPI'
        CARD = 'card', 'Credit/Debit Card'
        NETBANKING = 'netbanking', 'Net Banking'
        WALLET = 'wallet', 'Wallet'

    class CfStatus(models.TextChoices):
        CREATED = 'created', 'Created'
        AUTHORIZED = 'authorized', 'Authorized'
        CAPTURED = 'captured', 'Captured'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    booking: Booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='payments',
    )

    # ── Cashfree details ──
    cf_order_id: str = models.CharField(max_length=100, blank=True, null=True)
    cf_payment_id: str = models.CharField(max_length=100, blank=True, null=True)
    cf_payment_session_id: str = models.CharField(
        max_length=255, blank=True, null=True,
    )

    # ── Amount ──
    amount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2,
    )
    currency: str = models.CharField(max_length=3, default='INR')
    payment_type: str = models.CharField(
        max_length=20, choices=PaymentType.choices,
    )
    payment_method: str = models.CharField(
        max_length=30, choices=PaymentMethod.choices, blank=True, null=True,
    )

    # ── Status ──
    status: str = models.CharField(
        max_length=20, choices=CfStatus.choices, default=CfStatus.CREATED,
    )

    # ── Meta ──
    metadata: dict = models.JSONField(default=dict, blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['cf_order_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'payment_type'],
                condition=Q(status='created'),
                name='uniq_pending_payment_per_booking_type',
            ),
        ]

    def __str__(self) -> str:
        return f"Payment ₹{self.amount} for {self.booking.booking_number}"

    def save(self, *args, **kwargs) -> None:
        """Validate and save the payment."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        # Error Code: PAY-MODELS-VAL-001
        # Message: Payment amount must match booking amount
        # Cause: Mismatch detected
        # Solution: Check calculation logic
        if (self.amount is not None and self.booking_id
                and self.payment_type == 'full'
                and hasattr(self, 'booking') and self.booking
                and self.amount > self.booking.total_amount):
            raise DjangoValidationError(
                'Payment amount exceeds booking total.',
                code='PAY-MODELS-VAL-001',
            )

        # Error Code: PAY-MODELS-VAL-002
        # Message: Payment method required
        # Cause: Missing payment_method
        # Solution: Provide payment method
        # (Handled at serializer: payment_method has choices but is nullable)

        # Error Code: PAY-MODELS-CONFLICT-001
        # Message: Payment already processed for this booking
        # Cause: Duplicate payment attempt
        # Solution: Check payment.status
        if not self.pk and self.booking_id:
            existing = Payment.objects.filter(
                booking_id=self.booking_id,
                status__in=('captured', 'authorized'),
                payment_type=self.payment_type,
            ).exists()
            if existing:
                raise DjangoValidationError(
                    'Payment already processed for this booking.',
                    code='PAY-MODELS-CONFLICT-001',
                )

        self.full_clean()
        super().save(*args, **kwargs)


class BookingHistory(models.Model):
    """Track changes to booking status."""

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    booking: Booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='history',
    )
    old_status: str = models.CharField(
        max_length=30, choices=Booking.Status.choices, blank=True, default='',
        help_text='Empty on initial booking creation.',
    )
    new_status: str = models.CharField(max_length=30, choices=Booking.Status.choices)
    reason: str = models.TextField(blank=True, null=True)
    created_by: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking']),
        ]

    def __str__(self) -> str:
        return f"{self.booking.booking_number}: {self.old_status} → {self.new_status}"


# ──────────────────────────────────────────────────────────────────────────────
# Coupon models – PRD Section 4
# ──────────────────────────────────────────────────────────────────────────────

class Coupon(models.Model):
    """Discount coupons – PRD Section 4 (coupons table)."""

    class DiscountType(models.TextChoices):
        FLAT = 'flat', 'Flat Amount'
        PERCENTAGE = 'percentage', 'Percentage'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    code: str = models.CharField(max_length=20, unique=True)
    description: str = models.TextField(blank=True, null=True)
    discount_type: str = models.CharField(
        max_length=10, choices=DiscountType.choices,
    )
    discount_value: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2,
    )
    max_discount: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    min_booking: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    usage_limit: int = models.IntegerField(null=True, blank=True)
    used_count: int = models.IntegerField(default=0)
    per_user_limit: int = models.IntegerField(default=1)
    valid_from: models.DateTimeField = models.DateTimeField()
    valid_until: models.DateTimeField = models.DateTimeField()
    is_active: bool = models.BooleanField(default=True)

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.code} – {self.discount_type} {self.discount_value}"

    def save(self, *args, **kwargs) -> None:
        """Validate and save the coupon."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_valid(self) -> bool:
        """Check if the coupon is currently valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True


class CouponUsage(models.Model):
    """Track coupon usage per user/booking – PRD Section 4."""

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    coupon: Coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name='usages', db_index=True,
    )
    user: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='coupon_usages', db_index=True,
    )
    booking: Booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='coupon_usages', db_index=True,
    )
    discount_applied: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2,
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usage'
        unique_together = ('coupon', 'user', 'booking')

    def __str__(self) -> str:
        return f"{self.user} used {self.coupon.code} on {self.booking.booking_number}"
