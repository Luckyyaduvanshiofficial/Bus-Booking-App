import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings


ROLE_CHOICES = (
    ('customer', 'Customer'),
    ('operator', 'Bus Operator'),
    ('admin', 'Admin'),
)

VERIFICATION_STATUS = (
    ('pending', 'Pending'),
    ('verified', 'Verified'),
    ('rejected', 'Rejected'),
)

SUBSCRIPTION_TIER = (
    ('free', 'Free'),
    ('pro', 'Professional'),
    ('enterprise', 'Enterprise'),
)


class CustomUser(AbstractUser):
    """Custom user model with phone-based auth as specified in PRD Section 4."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be entered in format: +919829012345'
    )

    # Phone is primary identifier
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        blank=False,
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)

    # Role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    avatar_url = models.URLField(blank=True, null=True)

    # ── Operator-specific fields ──
    business_name = models.CharField(max_length=200, blank=True, null=True)
    business_type = models.CharField(
        max_length=50,
        choices=[('individual', 'Individual'), ('company', 'Company')],
        blank=True, null=True,
    )
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=15, blank=True, null=True)

    # Bank details
    bank_account = models.CharField(max_length=20, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=15, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)

    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # ── Operator verification ──
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS, default='pending',
    )
    rejection_reason = models.TextField(blank=True, null=True)

    # ── Platform data ──
    rating_avg = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    rating_count = models.IntegerField(default=0)
    total_bookings = models.IntegerField(default=0)
    total_buses = models.IntegerField(default=0)

    # ── Subscription (operators) ──
    subscription_tier = models.CharField(
        max_length=20, choices=SUBSCRIPTION_TIER, default='free',
    )
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=4, decimal_places=2, default=10.00)

    # ── Settings ──
    preferred_language = models.CharField(
        max_length=5,
        choices=[('hi', 'Hindi'), ('en', 'English')],
        default='hi',
    )
    is_active = models.BooleanField(default=True)

    # ── Supabase integration ──
    supabase_uid = models.CharField(max_length=255, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['role']),
            models.Index(fields=['city']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        display = self.name or self.get_full_name() or self.phone
        return f"{display} ({self.phone})"


# ──────────────────────────────────────────────────────────────────────────────
# Document model – operator documents for verification
# ──────────────────────────────────────────────────────────────────────────────

DOC_TYPES = (
    # Owner docs
    ('aadhar', 'Aadhaar Card'),
    ('pan', 'PAN Card'),
    ('bank_proof', 'Bank Proof'),
    # Bus docs
    ('rc', 'Registration Certificate'),
    ('fitness_certificate', 'Fitness Certificate'),
    ('permit', 'Bus Permit'),
    ('insurance', 'Insurance'),
    ('puc', 'PUC Certificate'),
    ('road_tax', 'Road Tax Receipt'),
    # Driver docs
    ('driver_license', 'Driver License'),
    ('driver_aadhar', 'Driver Aadhaar'),
    ('police_verification', 'Police Verification'),
    # Company docs
    ('gst_certificate', 'GST Certificate'),
    ('trade_license', 'Trade License'),
    ('company_registration', 'Company Registration'),
)


class Document(models.Model):
    """Operator documents for verification – PRD Section 4 (operator_documents)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    bus = models.ForeignKey(
        'buses.Bus',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='documents',
        help_text='NULL for owner-level docs; set for bus-specific docs.',
    )

    document_type = models.CharField(max_length=50, choices=DOC_TYPES)
    document_url = models.URLField()
    document_number = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Verification
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS, default='pending',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_documents',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'operator_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['bus']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.user} – {self.get_document_type_display()}"


# ──────────────────────────────────────────────────────────────────────────────
# Notification model
# ──────────────────────────────────────────────────────────────────────────────

NOTIFICATION_TYPES = (
    ('booking_confirmed', 'Booking Confirmed'),
    ('booking_cancelled', 'Booking Cancelled'),
    ('new_review', 'New Review'),
    ('payment_received', 'Payment Received'),
    ('document_verified', 'Document Verified'),
    ('document_rejected', 'Document Rejected'),
    ('operator_verified', 'Operator Verified'),
    ('payout_processed', 'Payout Processed'),
)


class Notification(models.Model):
    """Notifications for all user roles – PRD Section 4."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user} – {self.title}"
