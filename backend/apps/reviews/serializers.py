"""Review serializers with business-rule validation."""

from __future__ import annotations

from rest_framework import serializers

from .models import BusReview, OperatorReview


class BusReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_avatar = serializers.CharField(source='customer.avatar_url', read_only=True)
    bus_name = serializers.CharField(source='bus.name', read_only=True)

    class Meta:
        model = BusReview
        fields = [
            'id', 'booking', 'customer', 'customer_name', 'customer_avatar',
            'bus', 'bus_name', 'operator',
            'rating_overall', 'rating_cleanliness', 'rating_punctuality',
            'rating_driver', 'rating_value',
            'review_text', 'photo_urls',
            'is_approved', 'is_flagged',
            'created_at',
        ]
        read_only_fields = [
            'id', 'customer', 'bus', 'operator',
            'is_approved', 'is_flagged', 'created_at',
        ]


class BusReviewCreateSerializer(serializers.ModelSerializer):
    """Customer submits a review for a completed booking."""

    class Meta:
        model = BusReview
        fields = [
            'booking', 'rating_overall',
            'rating_cleanliness', 'rating_punctuality',
            'rating_driver', 'rating_value',
            'review_text', 'photo_urls',
        ]

    def validate_booking(self, booking):
        request = self.context.get('request')
        if booking.customer != request.user:
            # Error Code: REV-SERIAL-VAL-001
            # Message: Cannot review another user's booking
            # Cause: Authenticated user is not the booking customer
            # Solution: Only review bookings that belong to you
            raise serializers.ValidationError(
                "You can only review your own bookings.",
                code='REV-SERIAL-VAL-001',
            )
        if booking.status != 'completed':
            # Error Code: REV-SERIAL-VAL-002
            # Message: Booking not completed
            # Cause: Booking status is not 'completed'
            # Solution: Wait for the trip to be marked as completed
            raise serializers.ValidationError(
                "Only completed bookings can be reviewed.",
                code='REV-SERIAL-VAL-002',
            )
        if hasattr(booking, 'review'):
            # Error Code: REV-SERIAL-VAL-003
            # Message: Duplicate review
            # Cause: A review already exists for this booking
            # Solution: Each booking can only be reviewed once
            raise serializers.ValidationError(
                "This booking already has a review.",
                code='REV-SERIAL-VAL-003',
            )
        return booking


class OperatorReviewSerializer(serializers.ModelSerializer):
    """Serializer for OperatorReview (supports create/update).

    Writable fields: operator, reviewer, responsiveness_rating,
    professionalism_rating, reliability_rating, comment.
    Read-only fields: id, overall_rating, is_approved, created_at.
    """

    reviewer_name = serializers.CharField(source='reviewer.name', read_only=True)

    class Meta:
        model = OperatorReview
        fields = [
            'id', 'operator', 'reviewer', 'reviewer_name',
            'responsiveness_rating', 'professionalism_rating',
            'reliability_rating', 'overall_rating',
            'comment', 'is_approved', 'created_at',
        ]
        read_only_fields = ['id', 'reviewer', 'overall_rating', 'is_approved', 'created_at']

    def validate(self, attrs: dict) -> dict:
        """Ensure all sub-ratings are within valid range (1-5)."""
        for field in ('responsiveness_rating', 'professionalism_rating', 'reliability_rating'):
            value = attrs.get(field)
            if value is not None and not (1 <= value <= 5):
                # Error Code: REV-SERIAL-VAL-004
                # Message: Rating out of range
                # Cause: Sub-rating value is not between 1 and 5
                # Solution: Provide a rating between 1 and 5
                raise serializers.ValidationError(
                    {field: 'Rating must be between 1 and 5.'},
                    code='REV-SERIAL-VAL-004',
                )
        return attrs
