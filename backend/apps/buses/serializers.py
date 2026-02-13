from rest_framework import serializers
from .models import Bus, BusPhoto, BusAmenity, AvailabilityBlock


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
