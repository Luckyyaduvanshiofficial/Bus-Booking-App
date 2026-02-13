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
            raise serializers.ValidationError("You can only review your own bookings.")
        if booking.status != 'completed':
            raise serializers.ValidationError("Only completed bookings can be reviewed.")
        if hasattr(booking, 'review'):
            raise serializers.ValidationError("This booking already has a review.")
        return booking


class OperatorReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.name', read_only=True)

    class Meta:
        model = OperatorReview
        fields = [
            'id', 'operator', 'reviewer', 'reviewer_name',
            'responsiveness_rating', 'professionalism_rating',
            'reliability_rating', 'overall_rating',
            'comment', 'is_approved', 'created_at',
        ]
        read_only_fields = ['id', 'overall_rating', 'is_approved', 'created_at']
