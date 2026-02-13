import uuid
from django.db import models
from django.conf import settings


BUS_TYPES = (
    ('mini_bus', 'Mini Bus (17 seater)'),
    ('medium_bus', 'Medium Bus (25-30 seater)'),
    ('luxury_coach', 'Luxury Coach (40+ seater)'),
    ('tempo_traveller', 'Tempo Traveller'),
)

AC_TYPES = (
    ('ac', 'AC'),
    ('non_ac', 'Non-AC'),
    ('both', 'AC & Non-AC'),
)

FUEL_TYPES = (
    ('diesel', 'Diesel'),
    ('cng', 'CNG'),
    ('electric', 'Electric'),
)

PHOTO_TYPES = (
    ('exterior_front', 'Exterior Front'),
    ('exterior_side', 'Exterior Side'),
    ('interior', 'Interior'),
    ('seats', 'Seats'),
    ('dashboard', 'Dashboard'),
    ('other', 'Other'),
)

AMENITY_CHOICES = (
    ('music_system', 'Music System'),
    ('pushback_seats', 'Pushback Seats'),
    ('charging_points', 'Charging Points'),
    ('first_aid', 'First Aid Kit'),
    ('fire_extinguisher', 'Fire Extinguisher'),
    ('reading_lights', 'Reading Lights'),
    ('luggage_space', 'Luggage Space'),
    ('water_bottles', 'Water Bottles'),
    ('dj_system', 'DJ System'),
    ('wifi', 'WiFi'),
    ('tv_screen', 'TV Screen'),
    ('gps_tracking', 'GPS Tracking'),
    ('cctv', 'CCTV'),
    ('blankets_pillows', 'Blankets & Pillows'),
)

APPROVAL_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

BLOCK_REASONS = (
    ('booked_platform', 'Booked (Platform)'),
    ('booked_external', 'Booked (External)'),
    ('maintenance', 'Maintenance'),
    ('personal', 'Personal'),
)


class Bus(models.Model):
    """Bus model – PRD Section 4 (buses table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buses',
        limit_choices_to={'role': 'operator'},
    )

    # ── Basic info ──
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    bus_type = models.CharField(max_length=50, choices=BUS_TYPES)
    seating_capacity = models.IntegerField()

    # ── Vehicle details ──
    registration_number = models.CharField(max_length=20, unique=True)
    make_model = models.CharField(max_length=100, blank=True, null=True)
    manufacture_year = models.IntegerField(blank=True, null=True)
    ac_type = models.CharField(max_length=20, choices=AC_TYPES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='diesel')

    # ── Pricing ──
    price_per_km = models.DecimalField(max_digits=8, decimal_places=2)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    driver_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    night_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ── Location ──
    base_city = models.CharField(max_length=100, default='Jaipur')
    base_area = models.CharField(max_length=100, blank=True, null=True)

    # ── Status ──
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS, default='pending',
    )

    # ── Ratings ──
    rating_avg = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    rating_count = models.IntegerField(default=0)
    total_trips = models.IntegerField(default=0)

    # ── Meta ──
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'buses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operator']),
            models.Index(fields=['base_city']),
            models.Index(fields=['bus_type']),
            models.Index(fields=['seating_capacity']),
            models.Index(fields=['is_active', 'is_approved']),
        ]

    def __str__(self):
        return f"{self.name} ({self.registration_number})"


class BusPhoto(models.Model):
    """Bus photos – PRD Section 4 (bus_photos table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='photos')
    photo_url = models.URLField()
    photo_type = models.CharField(max_length=30, choices=PHOTO_TYPES)
    display_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bus_photos'
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['bus']),
        ]

    def __str__(self):
        return f"{self.bus.name} – {self.get_photo_type_display()}"


class BusAmenity(models.Model):
    """Amenities per bus – PRD Section 4 (bus_amenities table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='amenities')
    amenity = models.CharField(max_length=50, choices=AMENITY_CHOICES)

    class Meta:
        db_table = 'bus_amenities'
        unique_together = ('bus', 'amenity')
        indexes = [
            models.Index(fields=['bus']),
        ]

    def __str__(self):
        return f"{self.bus.name} – {self.get_amenity_display()}"


class AvailabilityBlock(models.Model):
    """Blocked dates per bus – PRD Section 4 (availability_blocks table).

    Uses a single blocked_date (DATE) per row with UNIQUE(bus, blocked_date).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='availability_blocks')
    blocked_date = models.DateField()
    block_reason = models.CharField(max_length=50, choices=BLOCK_REASONS)
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='blocked_dates',
        help_text='Set when blocked due to a platform booking.',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'availability_blocks'
        unique_together = ('bus', 'blocked_date')
        ordering = ['blocked_date']
        indexes = [
            models.Index(fields=['bus', 'blocked_date']),
        ]

    def __str__(self):
        return f"{self.bus.name} blocked on {self.blocked_date} ({self.get_block_reason_display()})"
