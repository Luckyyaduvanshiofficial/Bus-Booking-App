"""Bus, BusPhoto, BusAmenity, AvailabilityBlock serializers.

Each serializer declares explicit fields and uses validate() where needed.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import AvailabilityBlock, Bus, BusAmenity, BusPhoto


# ── Photo & Amenity ──────────────────────────────────────────

class BusPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusPhoto
        fields = ['id', 'photo_url', 'photo_type', 'display_order', 'is_primary']


class BusAmenitySerializer(serializers.ModelSerializer):
    amenity_display = serializers.CharField(source='get_amenity_display', read_only=True)

    class Meta:
        model = BusAmenity
        fields = ['id', 'amenity', 'amenity_display']


# ── AvailabilityBlock ────────────────────────────────────────

class AvailabilityBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        fields = ['id', 'blocked_date', 'block_reason', 'booking', 'created_at']
        read_only_fields = ['id', 'created_at']


class AvailabilityBlockCreateSerializer(serializers.ModelSerializer):
    """Operator blocks a date for a bus."""

    class Meta:
        model = AvailabilityBlock
        fields = ['blocked_date', 'block_reason']


# ── Bus ──────────────────────────────────────────────────────

class BusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list / search results."""
    primary_photo = serializers.SerializerMethodField()
    operator_name = serializers.CharField(source='operator.business_name', read_only=True)
    amenities = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            'id', 'name', 'bus_type', 'seating_capacity',
            'ac_type', 'price_per_km', 'base_price',
            'base_city', 'base_area',
            'rating_avg', 'rating_count',
            'operator_name', 'primary_photo', 'amenities',
            'is_active', 'is_approved',
        ]

    def get_primary_photo(self, obj):
        photo = obj.photos.filter(is_primary=True).first()
        if photo:
            return photo.photo_url
        photo = obj.photos.order_by('display_order').first()
        return photo.photo_url if photo else None

    def get_amenities(self, obj):
        return list(obj.amenities.values_list('amenity', flat=True))


class BusDetailSerializer(serializers.ModelSerializer):
    """Full bus detail with nested photos, amenities, availability."""
    photos = BusPhotoSerializer(many=True, read_only=True)
    amenities = BusAmenitySerializer(many=True, read_only=True)
    operator_name = serializers.CharField(source='operator.business_name', read_only=True)
    operator_rating = serializers.DecimalField(
        source='operator.rating_avg', max_digits=2, decimal_places=1, read_only=True,
    )
    blocked_dates = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            'id', 'operator', 'operator_name', 'operator_rating',
            'name', 'description', 'bus_type', 'seating_capacity',
            'registration_number', 'make_model', 'manufacture_year',
            'ac_type', 'fuel_type',
            'price_per_km', 'base_price', 'driver_charge', 'night_charge',
            'base_city', 'base_area',
            'is_active', 'is_approved', 'approval_status',
            'rating_avg', 'rating_count', 'total_trips',
            'photos', 'amenities', 'blocked_dates',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'rating_avg', 'rating_count', 'total_trips',
            'is_approved', 'approval_status', 'created_at', 'updated_at',
        ]

    def get_blocked_dates(self, obj):
        return list(
            obj.availability_blocks.values_list('blocked_date', flat=True)
        )


class BusCreateUpdateSerializer(serializers.ModelSerializer):
    """Operator creates / updates a bus."""

    class Meta:
        model = Bus
        fields = [
            'id', 'name', 'description', 'bus_type', 'seating_capacity',
            'registration_number', 'make_model', 'manufacture_year',
            'ac_type', 'fuel_type',
            'price_per_km', 'base_price', 'driver_charge', 'night_charge',
            'base_city', 'base_area',
        ]
        read_only_fields = ['id']

    def validate_seating_capacity(self, value: int) -> int:
        """Seating capacity must be realistic."""
        if value < 1:
            # Error Code: BUS-SERIAL-VAL-001
            # Message: Seating capacity too low
            # Cause: Value is less than 1
            # Solution: Set seating_capacity to at least 1
            raise serializers.ValidationError(
                'Seating capacity must be at least 1.',
                code='BUS-SERIAL-VAL-001',
            )
        if value > 100:
            # Error Code: BUS-SERIAL-VAL-002
            # Message: Seating capacity too high
            # Cause: Value exceeds maximum allowed (100)
            # Solution: Set seating_capacity to 100 or less
            raise serializers.ValidationError(
                'Seating capacity cannot exceed 100.',
                code='BUS-SERIAL-VAL-002',
            )
        return value

    def validate_price_per_km(self, value):
        """Price per km must be positive."""
        if value is not None and value <= 0:
            # Error Code: BUS-SERIAL-VAL-003
            # Message: Price per km must be positive
            # Cause: Zero or negative price_per_km provided
            # Solution: Set price_per_km to a positive value
            raise serializers.ValidationError(
                'Price per km must be positive.',
                code='BUS-SERIAL-VAL-003',
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """Cross-field validations for bus creation."""
        base_price = attrs.get('base_price')
        if base_price is not None and base_price < 0:
            # Error Code: BUS-SERIAL-VAL-004
            # Message: Base price cannot be negative
            # Cause: Negative base_price value provided
            # Solution: Set base_price to zero or a positive value
            raise serializers.ValidationError(
                {'base_price': 'Base price cannot be negative.'},
                code='BUS-SERIAL-VAL-004',
            )
        return attrs
