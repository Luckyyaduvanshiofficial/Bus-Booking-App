import uuid
from datetime import date
from django.db import models
from django.conf import settings
from django.utils import timezone


BOOKING_STATUS = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled_by_customer', 'Cancelled by Customer'),
    ('cancelled_by_operator', 'Cancelled by Operator'),
    ('expired', 'Expired'),
)

TRIP_TYPE = (
    ('one_way', 'One Way'),
    ('round_trip', 'Round Trip'),
    ('multi_day', 'Multi Day'),
)

BOOKING_PURPOSE = (
    ('wedding', 'Wedding'),
    ('religious', 'Religious Trip'),
    ('family_trip', 'Family Trip'),
    ('corporate', 'Corporate'),
    ('school_tour', 'School Tour'),
    ('other', 'Other'),
)

PAYMENT_MODE = (
    ('online_full', 'Pay Full Online'),
    ('online_advance', 'Pay Advance Online'),
    ('pay_driver', 'Pay Driver (Cash)'),
)

PAYMENT_STATUS = (
    ('pending', 'Pending'),
    ('advance_paid', 'Advance Paid'),
    ('fully_paid', 'Fully Paid'),
    ('refunded', 'Refunded'),
)

OPERATOR_RESPONSE = (
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
)

PAYOUT_STATUS = (
    ('pending', 'Pending'),
    ('processed', 'Processed'),
    ('paid', 'Paid'),
)

CF_PAYMENT_TYPE = (
    ('advance', 'Advance'),
    ('full', 'Full Payment'),
    ('remaining', 'Remaining Balance'),
    ('refund', 'Refund'),
)

CF_PAYMENT_METHOD = (
    ('upi', 'UPI'),
    ('card', 'Credit/Debit Card'),
    ('netbanking', 'Net Banking'),
    ('wallet', 'Wallet'),
)

CF_STATUS = (
    ('created', 'Created'),
    ('authorized', 'Authorized'),
    ('captured', 'Captured'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
)

DISCOUNT_TYPE = (
    ('flat', 'Flat Amount'),
    ('percentage', 'Percentage'),
)


class Booking(models.Model):
    """Booking model – PRD Section 4 (bookings table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking_number = models.CharField(max_length=20, unique=True, editable=False)

    # ── Parties ──
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='customer_bookings',
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='operator_bookings',
    )
    bus = models.ForeignKey(
        'buses.Bus', on_delete=models.CASCADE, related_name='bookings',
    )

    # ── Trip details ──
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE)
    pickup_location = models.TextField()
    pickup_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    pickup_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    drop_location = models.TextField()
    drop_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    drop_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    return_date = models.DateField(null=True, blank=True)
    passenger_count = models.IntegerField()
    purpose = models.CharField(max_length=50, choices=BOOKING_PURPOSE, blank=True, null=True)
    special_requests = models.TextField(blank=True, null=True)

    # ── Distance & route ──
    estimated_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_route = models.TextField(blank=True, null=True)

    # ── Pricing breakdown ──
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    driver_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    night_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    toll_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # ── Commission ──
    commission_rate = models.DecimalField(max_digits=4, decimal_places=2, default=10.00)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operator_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ── Status ──
    status = models.CharField(max_length=30, choices=BOOKING_STATUS, default='pending')

    # ── Operator response ──
    operator_response = models.CharField(
        max_length=20, choices=OPERATOR_RESPONSE, blank=True, null=True,
    )
    operator_response_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # ── Payment ──
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE, default='online_full')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ── Cancellation ──
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ── Completion ──
    completed_at = models.DateTimeField(null=True, blank=True)
    operator_payout_status = models.CharField(
        max_length=20, choices=PAYOUT_STATUS, default='pending',
    )
    operator_payout_at = models.DateTimeField(null=True, blank=True)

    # ── Meta ──
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return f"Booking {self.booking_number} – {self.customer}"

    def save(self, *args, **kwargs):
        if not self.booking_number:
            today = date.today().strftime('%Y%m%d')
            count = Booking.objects.filter(
                created_at__date=date.today()
            ).count() + 1
            self.booking_number = f"BK-{today}-{count:03d}"
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment record (Cashfree) – PRD Section 4 (payments table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='payments',
    )

    # ── Cashfree details ──
    cf_order_id = models.CharField(max_length=100, blank=True, null=True)
    cf_payment_id = models.CharField(max_length=100, blank=True, null=True)
    cf_payment_session_id = models.CharField(max_length=255, blank=True, null=True)

    # ── Amount ──
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_type = models.CharField(max_length=20, choices=CF_PAYMENT_TYPE)
    payment_method = models.CharField(
        max_length=30, choices=CF_PAYMENT_METHOD, blank=True, null=True,
    )

    # ── Status ──
    status = models.CharField(max_length=20, choices=CF_STATUS, default='created')

    # ── Meta ──
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['cf_order_id']),
        ]

    def __str__(self):
        return f"Payment ₹{self.amount} for {self.booking.booking_number}"


class BookingHistory(models.Model):
    """Track changes to booking status."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=30, choices=BOOKING_STATUS)
    new_status = models.CharField(max_length=30, choices=BOOKING_STATUS)
    reason = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking']),
        ]

    def __str__(self):
        return f"{self.booking.booking_number}: {self.old_status} → {self.new_status}"


# ──────────────────────────────────────────────────────────────────────────────
# Coupon models – PRD Section 4
# ──────────────────────────────────────────────────────────────────────────────

class Coupon(models.Model):
    """Discount coupons – PRD Section 4 (coupons table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_booking = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    per_user_limit = models.IntegerField(default=1)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} – {self.discount_type} {self.discount_value}"

    @property
    def is_valid(self):
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages',
    )
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name='coupon_usages',
    )
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usage'
        unique_together = ('coupon', 'user', 'booking')

    def __str__(self):
        return f"{self.user} used {self.coupon.code} on {self.booking.booking_number}"
