"""Booking, Payment, Coupon serializers.

Each serializer declares explicit fields and uses validate() for business rules.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import Booking, BookingHistory, Coupon, CouponUsage, Payment


# ── Payment ──────────────────────────────────────────────────


class PaymentSerializer(serializers.ModelSerializer):
    """Read-only payment representation.

    Hides raw Cashfree metadata from non-admin users to prevent
    exposure of sensitive payment gateway internals.
    """

    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'cf_order_id', 'cf_payment_id',
            'amount', 'currency', 'payment_type', 'payment_method',
            'status',
            'metadata', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'cf_order_id', 'cf_payment_id',
            'status', 'created_at', 'updated_at',
        ]

    def to_representation(self, instance):
        """Strip raw Cashfree metadata for non-admin users."""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or request.user.role != 'admin':
            data.pop('metadata', None)
        return data


class PaymentInitiateSerializer(serializers.Serializer):
    """Validate payload for payment initiation endpoint."""

    booking_id = serializers.UUIDField()
    payment_method = serializers.CharField(
        required=False,
        default=Payment.PaymentMethod.UPI,
    )

    def validate_payment_method(self, value: str) -> str:
        allowed = {choice[0] for choice in Payment.PaymentMethod.choices}
        if value not in allowed:
            raise serializers.ValidationError(
                'Unsupported payment method.',
                code='PAY-VIEWS-VAL-003',
            )
        return value


# ── Booking ──────────────────────────────────────────────────

class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight listing for dashboard / history."""
    bus_name = serializers.CharField(source='bus.name', read_only=True)
    bus_photo = serializers.SerializerMethodField()
    operator_name = serializers.CharField(
        source='operator.business_name', read_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'bus_name', 'bus_photo',
            'operator_name', 'trip_type',
            'pickup_location', 'drop_location',
            'pickup_date', 'return_date',
            'total_amount', 'status', 'payment_status',
            'created_at',
        ]
        read_only_fields = fields

    def get_bus_photo(self, obj):
        # Uses prefetch_related('bus__photos') from get_queryset
        # to avoid N+1 — iterating the prefetched set in Python
        photos = getattr(obj.bus, '_prefetched_objects_cache', {}).get('photos')
        if photos is None:
            photos = obj.bus.photos.all()
        for photo in photos:
            if photo.is_primary:
                return photo.photo_url
        return None


class BookingDetailSerializer(serializers.ModelSerializer):
    """Full booking detail with payments and history."""
    payments = PaymentSerializer(many=True, read_only=True)
    history = serializers.SerializerMethodField()
    bus_name = serializers.CharField(source='bus.name', read_only=True)
    operator_name = serializers.CharField(
        source='operator.business_name', read_only=True,
    )
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number',
            'customer', 'customer_name', 'customer_phone',
            'operator', 'operator_name',
            'bus', 'bus_name',
            # Trip
            'trip_type', 'pickup_location', 'pickup_lat', 'pickup_lng',
            'drop_location', 'drop_lat', 'drop_lng',
            'pickup_date', 'pickup_time', 'return_date',
            'passenger_count', 'purpose', 'special_requests',
            'estimated_km', 'estimated_route',
            # Pricing
            'base_amount', 'driver_charge', 'night_charge',
            'toll_estimate', 'platform_fee', 'discount_amount',
            'total_amount',
            # Commission
            'commission_rate', 'commission_amount', 'operator_payout',
            # Status
            'status', 'payment_status', 'payment_mode',
            'advance_amount',
            'operator_response', 'operator_response_at', 'rejection_reason',
            'operator_payout_status', 'operator_payout_at',
            # Cancellation
            'cancellation_reason', 'cancelled_at',
            'refund_amount',
            'completed_at',
            # Related
            'payments', 'history',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'booking_number', 'commission_rate', 'commission_amount',
            'operator_payout', 'platform_fee',
            'created_at', 'updated_at',
        ]

    def to_representation(self, instance):
        """Hide commission fields from customers — only visible to operator/admin."""
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.role == 'customer':
            data.pop('commission_rate', None)
            data.pop('commission_amount', None)
            data.pop('operator_payout', None)
            # Hide customer_phone for pending bookings (before confirmation)
            if instance.status == 'pending':
                data.pop('customer_phone', None)
        return data

    def get_history(self, obj):
        prefetched = getattr(obj, '_prefetched_objects_cache', {}).get('history')
        if prefetched is not None:
            history_items = sorted(
                prefetched,
                key=lambda item: item.created_at,
                reverse=True,
            )
            return BookingHistorySerializer(history_items, many=True).data

        qs = obj.history.order_by('-created_at')
        return BookingHistorySerializer(qs, many=True).data


class BookingCreateSerializer(serializers.ModelSerializer):
    """Customer creates a new booking."""

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'bus', 'trip_type',
            'pickup_location', 'pickup_lat', 'pickup_lng',
            'drop_location', 'drop_lat', 'drop_lng',
            'pickup_date', 'pickup_time', 'return_date',
            'passenger_count', 'purpose', 'special_requests',
            'estimated_km', 'estimated_route',
            'payment_mode',
            'total_amount', 'status',
        ]
        read_only_fields = ['id', 'booking_number', 'total_amount', 'status']

    def validate(self, attrs: dict) -> dict:
        """Validate booking business rules."""
        bus = attrs.get('bus')
        if bus and not bus.is_active:
            # Error Code: BOK-SERIAL-VAL-001
            # Message: Bus is no longer active
            # Cause: The selected bus has been deactivated
            # Solution: Choose a different active bus
            raise serializers.ValidationError(
                {'bus': 'This bus is no longer active.'},
                code='BOK-SERIAL-VAL-001',
            )
        if bus and not bus.is_approved:
            # Error Code: BOK-SERIAL-VAL-002
            # Message: Bus not yet approved
            # Cause: The selected bus is pending admin approval
            # Solution: Choose an approved bus or wait for approval
            raise serializers.ValidationError(
                {'bus': 'This bus has not been approved yet.'},
                code='BOK-SERIAL-VAL-002',
            )

        passenger_count = attrs.get('passenger_count')
        if passenger_count is not None and passenger_count == 0:
            raise serializers.ValidationError(
                {'passenger_count': 'Must be at least 1.'},
                code='BOK-SERIAL-VAL-006',
            )
        if bus and passenger_count is not None and passenger_count > bus.seating_capacity:
            # Error Code: BOK-SERIAL-VAL-003
            # Message: Passenger count exceeds bus capacity
            # Cause: More passengers selected than bus can hold
            # Solution: Choose a larger bus or reduce passenger count
            raise serializers.ValidationError(
                {'passenger_count': f'Exceeds bus capacity of {bus.seating_capacity}.'},
                code='BOK-SERIAL-VAL-003',
            )

        pickup_date = attrs.get('pickup_date')
        return_date = attrs.get('return_date')
        if pickup_date and return_date and return_date < pickup_date:
            # Error Code: BOK-SERIAL-VAL-004
            # Message: Return date before pickup date
            # Cause: Invalid date range — return_date < pickup_date
            # Solution: Set return_date after pickup_date
            raise serializers.ValidationError(
                {'return_date': 'Return date cannot be before pickup date.'},
                code='BOK-SERIAL-VAL-004',
            )

        trip_type = attrs.get('trip_type')
        if trip_type == 'round_trip' and not return_date:
            # Error Code: BOK-SERIAL-VAL-005
            # Message: Return date required for round trips
            # Cause: Round trip selected but no return_date provided
            # Solution: Provide a return_date for round trip bookings
            raise serializers.ValidationError(
                {'return_date': 'Return date is required for round trips.'},
                code='BOK-SERIAL-VAL-005',
            )

        return attrs


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Operator / Admin updates booking status.

    Accepts 'confirmed' or 'rejected' for operator respond action.
    The service layer maps 'rejected' to the appropriate internal status.

    Error Codes:
        BOK-SERIAL-VAL-007: Invalid status transition value
    """

    # Error Code: BOK-SERIAL-VAL-007
    # Message: Invalid status value for respond action
    # Cause: Status must be 'confirmed' or 'rejected'
    # Solution: Pass status='confirmed' or status='rejected'
    RESPOND_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    status = serializers.ChoiceField(
        choices=RESPOND_CHOICES,
        required=True,
        help_text="New booking status: 'confirmed' or 'rejected'.",
    )
    reason = serializers.CharField(
        required=False, allow_blank=True,
        help_text='Optional reason for the status change (e.g. rejection reason).',
    )


# ── History ──────────────────────────────────────────────────

class BookingHistorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.name', read_only=True,
    )

    class Meta:
        model = BookingHistory
        fields = [
            'id', 'old_status', 'new_status',
            'reason', 'created_by_name', 'created_at',
        ]
        read_only_fields = fields


# ── Coupon ───────────────────────────────────────────────────

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description',
            'discount_type', 'discount_value', 'max_discount',
            'min_booking', 'usage_limit', 'used_count',
            'per_user_limit', 'valid_from', 'valid_until',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'used_count', 'created_at']


class CouponApplySerializer(serializers.Serializer):
    """Customer applies a coupon to a booking."""
    code = serializers.CharField(max_length=30)
    booking_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
