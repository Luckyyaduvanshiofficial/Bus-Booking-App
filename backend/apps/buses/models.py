"""Bus models – PRD Section 4.

Bus, BusPhoto, BusAmenity, and AvailabilityBlock models.
"""

from __future__ import annotations

import datetime as dt
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Bus(models.Model):
    """Bus model – PRD Section 4 (buses table)."""

    class BusType(models.TextChoices):
        MINI_BUS = 'mini_bus', 'Mini Bus (17 seater)'
        MEDIUM_BUS = 'medium_bus', 'Medium Bus (25-30 seater)'
        LUXURY_COACH = 'luxury_coach', 'Luxury Coach (40+ seater)'
        TEMPO_TRAVELLER = 'tempo_traveller', 'Tempo Traveller'

    class AcType(models.TextChoices):
        AC = 'ac', 'AC'
        NON_AC = 'non_ac', 'Non-AC'
        BOTH = 'both', 'AC & Non-AC'

    class FuelType(models.TextChoices):
        DIESEL = 'diesel', 'Diesel'
        CNG = 'cng', 'CNG'
        ELECTRIC = 'electric', 'Electric'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    operator: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buses',
        db_index=True,
        limit_choices_to={'role': 'operator'},
    )

    # ── Basic info ──
    name: str = models.CharField(max_length=200)
    description: str = models.TextField(blank=True, null=True)
    bus_type: str = models.CharField(max_length=50, choices=BusType.choices)
    seating_capacity: int = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    # ── Vehicle details ──
    registration_number: str = models.CharField(max_length=20, unique=True)
    make_model: str = models.CharField(max_length=100, blank=True, null=True)
    manufacture_year: int = models.IntegerField(blank=True, null=True)
    ac_type: str = models.CharField(max_length=20, choices=AcType.choices)
    fuel_type: str = models.CharField(
        max_length=20, choices=FuelType.choices, default=FuelType.DIESEL,
    )

    # ── Pricing ──
    price_per_km: models.DecimalField = models.DecimalField(
        max_digits=8, decimal_places=2,
    )
    base_price: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    driver_charge: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )
    night_charge: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
    )

    # ── Location ──
    base_city: str = models.CharField(max_length=100, default='Jaipur')
    base_area: str = models.CharField(max_length=100, blank=True, null=True)

    # ── Status ──
    is_active: bool = models.BooleanField(default=True)
    approval_status: str = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING,
    )

    @property
    def is_approved(self) -> bool:
        """Derive approval state from approval_status."""
        return self.approval_status == 'approved'

    # ── Ratings ──
    rating_avg: models.DecimalField = models.DecimalField(
        max_digits=3, decimal_places=1, default=0.0,
    )
    rating_count: int = models.IntegerField(default=0)
    total_trips: int = models.IntegerField(default=0)

    # ── Meta ──
    created_at: dt.datetime = models.DateTimeField(auto_now_add=True)
    updated_at: dt.datetime = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'buses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operator']),
            models.Index(fields=['base_city']),
            models.Index(fields=['bus_type']),
            models.Index(fields=['seating_capacity']),
            models.Index(fields=['is_active', 'approval_status']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.registration_number})"

    def clean(self) -> None:
        """Model-level validation with error codes from ERROR_REGISTRY.md."""
        super().clean()
        from django.core.exceptions import ValidationError

        # Error Code: BUS-MODELS-VAL-001
        # Message: Bus name required (max 200 characters)
        # Cause: Empty or too long name
        # Solution: Check Bus.name field
        if not self.name or not self.name.strip():
            raise ValidationError(
                'Bus name is required.',
                code='BUS-MODELS-VAL-001',
            )

        # Error Code: BUS-MODELS-VAL-002
        # Message: Capacity must be between 1 and 60 seats
        # Cause: Invalid capacity value
        # Solution: Check seating_capacity field
        if self.seating_capacity is not None and self.seating_capacity > 60:
            raise ValidationError(
                'Seating capacity cannot exceed 60.',
                code='BUS-MODELS-VAL-002',
            )

        # Error Code: BUS-MODELS-VAL-003
        # Message: Base price must be positive
        # Cause: Negative price entered
        # Solution: Check base_price >= 0
        if self.base_price is not None and self.base_price < 0:
            raise ValidationError(
                'Base price must be zero or positive.',
                code='BUS-MODELS-VAL-003',
            )

    def save(self, *args, **kwargs) -> None:
        """Validate and save the bus.

        Skips full_clean() when update_fields is provided (e.g.,
        rating updates) to avoid validating ALL fields when only
        specific fields are being updated.
        """
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)

    # ── Business methods ──

    def is_available_on(self, date: dt.date) -> bool:
        """Check if bus is available on a given date.

        Args:
            date: The date to check availability for.

        Returns:
            True if no availability block exists for the date.
        """
        return not self.availability_blocks.filter(blocked_date=date).exists()

    def calculate_trip_cost(self, estimated_km: int) -> dict:
        """Calculate estimated trip cost breakdown.

        Args:
            estimated_km: Estimated distance in kilometers.

        Returns:
            Dict with base, distance, driver, night, and total charges.
        """
        from decimal import Decimal
        base = self.base_price or Decimal('0')
        distance = Decimal(str(estimated_km)) * (self.price_per_km or Decimal('0'))
        return {
            'base_price': base,
            'distance_charge': distance,
            'driver_charge': self.driver_charge or Decimal('0'),
            'night_charge': self.night_charge or Decimal('0'),
            'estimated_total': base + distance + (self.driver_charge or Decimal('0')) + (self.night_charge or Decimal('0')),
        }


class BusPhoto(models.Model):
    """Bus photos – PRD Section 4 (bus_photos table)."""

    class PhotoType(models.TextChoices):
        EXTERIOR_FRONT = 'exterior_front', 'Exterior Front'
        EXTERIOR_SIDE = 'exterior_side', 'Exterior Side'
        INTERIOR = 'interior', 'Interior'
        SEATS = 'seats', 'Seats'
        DASHBOARD = 'dashboard', 'Dashboard'
        OTHER = 'other', 'Other'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    bus: Bus = models.ForeignKey(
        Bus, on_delete=models.CASCADE, related_name='photos', db_index=True,
    )
    photo_url: str = models.URLField()
    photo_type: str = models.CharField(max_length=30, choices=PhotoType.choices)
    display_order: int = models.IntegerField(default=0)
    is_primary: bool = models.BooleanField(default=False)

    created_at: dt.datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bus_photos'
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['bus']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['bus'],
                condition=Q(is_primary=True),
                name='unique_primary_photo_per_bus',
            ),
        ]

    def __str__(self) -> str:
        return f"{self.bus.name} – {self.get_photo_type_display()}"

    def save(self, *args, **kwargs) -> None:
        """Validate and save the photo."""
        self.full_clean()
        super().save(*args, **kwargs)


class BusAmenity(models.Model):
    """Amenities per bus – PRD Section 4 (bus_amenities table)."""

    class AmenityType(models.TextChoices):
        MUSIC_SYSTEM = 'music_system', 'Music System'
        PUSHBACK_SEATS = 'pushback_seats', 'Pushback Seats'
        CHARGING_POINTS = 'charging_points', 'Charging Points'
        FIRST_AID = 'first_aid', 'First Aid Kit'
        FIRE_EXTINGUISHER = 'fire_extinguisher', 'Fire Extinguisher'
        READING_LIGHTS = 'reading_lights', 'Reading Lights'
        LUGGAGE_SPACE = 'luggage_space', 'Luggage Space'
        WATER_BOTTLES = 'water_bottles', 'Water Bottles'
        DJ_SYSTEM = 'dj_system', 'DJ System'
        WIFI = 'wifi', 'WiFi'
        TV_SCREEN = 'tv_screen', 'TV Screen'
        GPS_TRACKING = 'gps_tracking', 'GPS Tracking'
        CCTV = 'cctv', 'CCTV'
        BLANKETS_PILLOWS = 'blankets_pillows', 'Blankets & Pillows'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    bus: Bus = models.ForeignKey(
        Bus, on_delete=models.CASCADE, related_name='amenities', db_index=True,
    )
    amenity: str = models.CharField(max_length=50, choices=AmenityType.choices)

    class Meta:
        db_table = 'bus_amenities'
        unique_together = ('bus', 'amenity')
        indexes = [
            models.Index(fields=['bus']),
        ]

    def __str__(self) -> str:
        return f"{self.bus.name} – {self.get_amenity_display()}"


class AvailabilityBlock(models.Model):
    """Blocked dates per bus – PRD Section 4 (availability_blocks table).

    Uses a single blocked_date (DATE) per row with UNIQUE(bus, blocked_date).
    """

    class BlockReason(models.TextChoices):
        BOOKED_PLATFORM = 'booked_platform', 'Booked (Platform)'
        BOOKED_EXTERNAL = 'booked_external', 'Booked (External)'
        MAINTENANCE = 'maintenance', 'Maintenance'
        PERSONAL = 'personal', 'Personal'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    bus: Bus = models.ForeignKey(
        Bus, on_delete=models.CASCADE, related_name='availability_blocks', db_index=True,
    )
    blocked_date: dt.date = models.DateField()
    block_reason: str = models.CharField(
        max_length=50, choices=BlockReason.choices,
    )
    booking: models.ForeignKey = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='blocked_dates',
        help_text='Set when blocked due to a platform booking.',
    )
    notes: str = models.TextField(
        blank=True, null=True,
        help_text='Optional notes for manual blocks (e.g., maintenance details)',
    )

    created_at: dt.datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'availability_blocks'
        unique_together = ('bus', 'blocked_date')
        ordering = ['blocked_date']
        indexes = [
            models.Index(fields=['bus', 'blocked_date']),
        ]

    def __str__(self) -> str:
        return f"{self.bus.name} blocked on {self.blocked_date} ({self.get_block_reason_display()})"
