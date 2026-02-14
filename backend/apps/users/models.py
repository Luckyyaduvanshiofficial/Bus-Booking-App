"""User models – PRD Section 4.

CustomUser, Document, and Notification models with phone-based auth.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUser(AbstractUser):
    """Custom user model with phone-based auth as specified in PRD Section 4."""

    _ENCRYPTED_PREFIX = 'enc::'

    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        OPERATOR = 'operator', 'Bus Operator'
        ADMIN = 'admin', 'Admin'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'

    class SubscriptionTier(models.TextChoices):
        FREE = 'free', 'Free'
        PRO = 'pro', 'Professional'
        ENTERPRISE = 'enterprise', 'Enterprise'

    class BusinessType(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual'
        COMPANY = 'company', 'Company'

    class Language(models.TextChoices):
        HINDI = 'hi', 'Hindi'
        ENGLISH = 'en', 'English'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be entered in format: +919829012345',
    )

    # Phone is primary identifier
    phone: str = models.CharField(
        validators=[phone_regex], max_length=15, unique=True, blank=False,
    )
    name: str = models.CharField(max_length=100, blank=True, null=True)
    email: str = models.EmailField(max_length=255, blank=True, null=True)

    # Role
    role: str = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CUSTOMER,
    )
    avatar_url: str = models.URLField(blank=True, null=True)

    # ── Operator-specific fields ──
    business_name: str = models.CharField(max_length=200, blank=True, null=True)
    business_type: str = models.CharField(
        max_length=50, choices=BusinessType.choices, blank=True, null=True,
    )
    gst_number: str = models.CharField(max_length=20, blank=True, null=True)
    pan_number: str = models.CharField(max_length=255, blank=True, null=True)

    # Bank details
    bank_account: str = models.CharField(max_length=255, blank=True, null=True)
    bank_ifsc: str = models.CharField(max_length=15, blank=True, null=True)
    bank_name: str = models.CharField(max_length=100, blank=True, null=True)

    address: str = models.TextField(blank=True, null=True)
    city: str = models.CharField(max_length=100, blank=True, null=True)

    # ── Operator verification ──
    is_verified: bool = models.BooleanField(default=False)
    verified_at: datetime = models.DateTimeField(null=True, blank=True)
    verification_status: str = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    rejection_reason: str = models.TextField(blank=True, null=True)

    # ── Platform data ──
    rating_avg: models.DecimalField = models.DecimalField(
        max_digits=3, decimal_places=1, default=0.0,
    )
    rating_count: int = models.IntegerField(default=0)
    total_bookings: int = models.IntegerField(default=0)
    total_buses: int = models.IntegerField(default=0)

    # ── Subscription (operators) ──
    subscription_tier: str = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE,
    )
    subscription_expires_at: datetime = models.DateTimeField(null=True, blank=True)
    commission_rate: models.DecimalField = models.DecimalField(
        max_digits=4, decimal_places=2, default=10.00,
    )

    # ── Settings ──
    preferred_language: str = models.CharField(
        max_length=5, choices=Language.choices, default=Language.HINDI,
    )
    is_active: bool = models.BooleanField(default=True)

    # ── Supabase integration ──
    supabase_uid: str = models.CharField(
        max_length=255, blank=True, null=True, unique=True,
    )

    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

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

    def __str__(self) -> str:
        display = self.name or self.get_full_name() or self.phone
        return f"{display} ({self.phone})"

    def clean(self) -> None:
        """Model-level validation with error codes from ERROR_REGISTRY.md."""
        super().clean()
        from django.core.exceptions import ValidationError

        # Error Code: USR-MODELS-VAL-001
        # Message: Phone number must be 10 digits
        # Cause: Invalid phone format
        # Solution: Check phone_number field validation
        if self.phone:
            cleaned = self.phone.strip().lstrip('+')
            if not cleaned.isdigit() or len(cleaned) < 10 or len(cleaned) > 15:
                raise ValidationError(
                    'Phone must be 10-15 digits.',
                    code='USR-MODELS-VAL-001',
                )

        # Error Code: USR-MODELS-VAL-002
        # Message: Invalid user role
        # Cause: Role field has invalid value
        # Solution: Check User.Role.choices
        valid_roles = {c[0] for c in self.Role.choices}
        if self.role and self.role not in valid_roles:
            raise ValidationError(
                f'Invalid role. Must be one of: {valid_roles}',
                code='USR-MODELS-VAL-002',
            )

    def save(self, *args, **kwargs) -> None:
        """Validate and save the user.

        Skips validation when ``skip_validation=True`` is passed (e.g.
        from Django's ``create_superuser`` machinery).  Always excludes
        the ``password`` field from ``full_clean`` because OTP-based
        auth does not require passwords.
        """
        self.bank_account = self._encrypt_sensitive(self.bank_account)
        self.pan_number = self._encrypt_sensitive(self.pan_number)
        if not kwargs.pop('skip_validation', False):
            self.full_clean(exclude=['password'])
        super().save(*args, **kwargs)

    # ── Business methods ──

    @property
    def is_operator(self) -> bool:
        """Check if user has operator role."""
        return self.role == self.Role.OPERATOR

    @property
    def is_customer(self) -> bool:
        """Check if user has customer role."""
        return self.role == self.Role.CUSTOMER

    @property
    def is_admin_user(self) -> bool:
        """Check if user has admin role."""
        return self.role == self.Role.ADMIN

    def has_active_subscription(self) -> bool:
        """Check if operator has an active paid subscription."""
        if self.subscription_tier == self.SubscriptionTier.FREE:
            return False
        from django.utils import timezone
        return (
            self.subscription_expires_at is not None
            and self.subscription_expires_at > timezone.now()
        )

    @classmethod
    def _get_fernet(cls):
        key = (getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or '').strip()
        if not key:
            return None

        key_bytes = key.encode('utf-8')
        try:
            return Fernet(key_bytes)
        except Exception:
            derived = base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())
            return Fernet(derived)

    @classmethod
    def _encrypt_sensitive(cls, value: str | None) -> str | None:
        if value in (None, ''):
            return value
        text = str(value)
        if text.startswith(cls._ENCRYPTED_PREFIX):
            return text
        fernet = cls._get_fernet()
        if not fernet:
            return text
        encrypted = fernet.encrypt(text.encode('utf-8')).decode('utf-8')
        return f'{cls._ENCRYPTED_PREFIX}{encrypted}'

    @classmethod
    def _decrypt_sensitive(cls, value: str | None) -> str:
        if not value:
            return ''
        text = str(value)
        if not text.startswith(cls._ENCRYPTED_PREFIX):
            return text

        fernet = cls._get_fernet()
        if not fernet:
            return ''
        token = text[len(cls._ENCRYPTED_PREFIX):]
        try:
            return fernet.decrypt(token.encode('utf-8')).decode('utf-8')
        except (InvalidToken, ValueError):
            return ''

    def get_bank_account_plain(self) -> str:
        return self._decrypt_sensitive(self.bank_account)

    def get_pan_number_plain(self) -> str:
        return self._decrypt_sensitive(self.pan_number)


# ──────────────────────────────────────────────────────────────────────────────
# Document model – operator documents for verification
# ──────────────────────────────────────────────────────────────────────────────


class Document(models.Model):
    """Operator documents for verification – PRD Section 4 (operator_documents)."""

    class DocumentType(models.TextChoices):
        # Owner docs
        AADHAR = 'aadhar', 'Aadhaar Card'
        PAN = 'pan', 'PAN Card'
        BANK_PROOF = 'bank_proof', 'Bank Proof'
        # Bus docs
        RC = 'rc', 'Registration Certificate'
        FITNESS_CERTIFICATE = 'fitness_certificate', 'Fitness Certificate'
        PERMIT = 'permit', 'Bus Permit'
        INSURANCE = 'insurance', 'Insurance'
        PUC = 'puc', 'PUC Certificate'
        ROAD_TAX = 'road_tax', 'Road Tax Receipt'
        # Driver docs
        DRIVER_LICENSE = 'driver_license', 'Driver License'
        DRIVER_AADHAR = 'driver_aadhar', 'Driver Aadhaar'
        POLICE_VERIFICATION = 'police_verification', 'Police Verification'
        # Company docs
        GST_CERTIFICATE = 'gst_certificate', 'GST Certificate'
        TRADE_LICENSE = 'trade_license', 'Trade License'
        COMPANY_REGISTRATION = 'company_registration', 'Company Registration'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    user: CustomUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    bus: models.ForeignKey = models.ForeignKey(
        'buses.Bus',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='documents',
        help_text='NULL for owner-level docs; set for bus-specific docs.',
    )

    document_type: str = models.CharField(
        max_length=50, choices=DocumentType.choices,
    )
    document_url: str = models.URLField()
    document_number: str = models.CharField(max_length=50, blank=True, null=True)
    expiry_date: models.DateField = models.DateField(null=True, blank=True)

    # Verification
    verification_status: str = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_by: CustomUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_documents',
    )
    verified_at: datetime = models.DateTimeField(null=True, blank=True)
    rejection_reason: str = models.TextField(blank=True, null=True)

    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'operator_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['bus']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self) -> str:
        return f"{self.user} – {self.get_document_type_display()}"

    def clean(self) -> None:
        """Model-level validation with error codes from ERROR_REGISTRY.md."""
        super().clean()
        from django.core.exceptions import ValidationError

        # Error Code: DOC-MODELS-VAL-001
        # Message: Document type required
        # Cause: Missing doc_type
        # Solution: Specify document type
        if not self.document_type:
            raise ValidationError(
                'Document type is required.',
                code='DOC-MODELS-VAL-001',
            )

        # Error Code: DOC-MODELS-VAL-002
        # Message: Expiry date must be in future
        # Cause: Expired document uploaded
        # Solution: Upload valid document
        if self.expiry_date:
            from datetime import date
            if self.expiry_date < date.today():
                raise ValidationError(
                    'Expiry date must be in the future.',
                    code='DOC-MODELS-VAL-002',
                )

        # Error Code: DOC-MODELS-VAL-003
        # Message: Document file required
        # Cause: No file uploaded
        # Solution: Upload PDF/image file
        if not self.document_url:
            raise ValidationError(
                'Document URL is required.',
                code='DOC-MODELS-VAL-003',
            )

    def save(self, *args, **kwargs) -> None:
        """Validate and save the document."""
        self.full_clean()
        super().save(*args, **kwargs)

    # ── Business methods ──

    @property
    def is_expired(self) -> bool:
        """Check if the document has expired."""
        if self.expiry_date is None:
            return False
        from datetime import date
        return self.expiry_date < date.today()

    @property
    def is_verified_status(self) -> bool:
        """Check if the document is verified."""
        return self.verification_status == self.VerificationStatus.VERIFIED


# ──────────────────────────────────────────────────────────────────────────────
# Notification model
# ──────────────────────────────────────────────────────────────────────────────


class Notification(models.Model):
    """Notifications for all user roles – PRD Section 4."""

    class NotificationType(models.TextChoices):
        BOOKING_CONFIRMED = 'booking_confirmed', 'Booking Confirmed'
        BOOKING_CANCELLED = 'booking_cancelled', 'Booking Cancelled'
        NEW_REVIEW = 'new_review', 'New Review'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        DOCUMENT_VERIFIED = 'document_verified', 'Document Verified'
        DOCUMENT_REJECTED = 'document_rejected', 'Document Rejected'
        OPERATOR_VERIFIED = 'operator_verified', 'Operator Verified'
        OPERATOR_REJECTED = 'operator_rejected', 'Operator Rejected'
        PAYOUT_PROCESSED = 'payout_processed', 'Payout Processed'

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    user: CustomUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
    )
    type: str = models.CharField(
        max_length=50, choices=NotificationType.choices,
    )
    title: str = models.CharField(max_length=200)
    message: str = models.TextField()
    is_read: bool = models.BooleanField(default=False)
    metadata: dict = models.JSONField(default=dict, blank=True)

    created_at: datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self) -> str:
        return f"{self.user} – {self.title}"

    def save(self, *args, **kwargs) -> None:
        """Validate and save the notification."""
        self.full_clean()
        super().save(*args, **kwargs)
