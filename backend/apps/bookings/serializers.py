from rest_framework import serializers
from .models import Booking, Payment, BookingHistory, Coupon, CouponUsage


# ── Payment ──────────────────────────────────────────────────

class PaymentSerializer(serializers.ModelSerializer):
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
        photo = obj.bus.photos.filter(is_primary=True).first()
        return photo.photo_url if photo else None


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

    def get_history(self, obj):
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


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Operator / Admin updates booking status."""
    status = serializers.ChoiceField(
        choices=['confirmed', 'rejected', 'completed', 'cancelled'],
    )
    reason = serializers.CharField(required=False, allow_blank=True)


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
