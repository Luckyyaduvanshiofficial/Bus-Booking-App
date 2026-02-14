"""User, Operator, Document, Notification and Auth serializers.

Each serializer declares explicit fields and applies validate() where needed.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import CustomUser, Document, Notification


# ── User Serializers ──────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """Public-safe user representation."""

    class Meta:
        model = CustomUser
        fields = [
            'id', 'phone', 'name', 'email', 'role',
            'avatar_url', 'is_verified', 'verification_status',
            'rating_avg', 'rating_count', 'total_bookings',
            'preferred_language', 'created_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'is_verified', 'verification_status',
            'rating_avg', 'rating_count', 'total_bookings',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile for the authenticated user."""

    class Meta:
        model = CustomUser
        fields = [
            'id', 'phone', 'name', 'email', 'role',
            'avatar_url', 'is_verified', 'verification_status',
            'preferred_language', 'total_bookings',
            'rating_avg', 'rating_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'phone', 'role', 'is_verified', 'verification_status',
            'rating_avg', 'rating_count', 'total_bookings',
            'created_at', 'updated_at',
        ]


class OperatorSerializer(serializers.ModelSerializer):
    """Full operator representation — ONLY for admin or the operator themselves."""
    documents = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'phone', 'name', 'email',
            'business_name', 'business_type',
            'gst_number', 'pan_number',
            'bank_account', 'bank_ifsc', 'bank_name',
            'address', 'city',
            'is_verified', 'verification_status', 'rejection_reason',
            'rating_avg', 'rating_count',
            'subscription_tier', 'commission_rate',
            'total_buses', 'total_bookings',
            'documents', 'created_at',
        ]
        read_only_fields = [
            'id', 'is_verified', 'verification_status',
            'rating_avg', 'rating_count',
            'total_buses', 'total_bookings', 'created_at',
        ]

    def get_documents(self, obj):
        return DocumentSerializer(obj.documents.all(), many=True).data

    def to_representation(self, instance):
        """Mask sensitive financial fields in responses."""
        data = super().to_representation(instance)

        bank_account = instance.get_bank_account_plain()
        if bank_account:
            if len(bank_account) <= 4:
                data['bank_account'] = '*' * len(bank_account)
            else:
                data['bank_account'] = ('*' * (len(bank_account) - 4)) + bank_account[-4:]
        else:
            data['bank_account'] = ''

        pan = instance.get_pan_number_plain()
        if pan:
            if len(pan) <= 4:
                data['pan_number'] = '*' * len(pan)
            else:
                data['pan_number'] = ('*' * (len(pan) - 4)) + pan[-4:]
        else:
            data['pan_number'] = ''
        return data


class OperatorPublicSerializer(serializers.ModelSerializer):
    """Public-safe operator representation — no financial or PII fields."""

    class Meta:
        model = CustomUser
        fields = [
            'id', 'business_name', 'business_type',
            'city', 'is_verified',
            'rating_avg', 'rating_count',
            'total_buses', 'total_bookings',
        ]
        read_only_fields = fields


class OperatorRegistrationSerializer(serializers.ModelSerializer):
    """Used during operator on-boarding (POST only).

    Phone is read-only because the user's phone is already set from
    OTP verification and must not be changed without re-verification.
    """

    class Meta:
        model = CustomUser
        fields = [
            'phone', 'name', 'email',
            'business_name', 'business_type',
            'gst_number', 'pan_number',
            'bank_account', 'bank_ifsc', 'bank_name',
            'address', 'city',
        ]
        read_only_fields = ['phone']


# ── Document Serializers ─────────────────────────────────────

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'user', 'bus', 'document_type', 'document_url',
            'document_number', 'expiry_date',
            'verification_status', 'verified_by', 'verified_at',
            'rejection_reason', 'created_at',
        ]
        read_only_fields = [
            'id', 'verification_status', 'verified_by',
            'verified_at', 'rejection_reason', 'created_at',
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Minimal fields for document upload."""

    class Meta:
        model = Document
        fields = [
            'id', 'bus', 'document_type', 'document_url',
            'document_number', 'expiry_date',
        ]
        read_only_fields = ['id']


class DocumentVerifySerializer(serializers.Serializer):
    """Admin action to approve / reject a document."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


# ── Notification Serializers ─────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message',
            'is_read', 'metadata', 'created_at',
        ]
        read_only_fields = ['id', 'type', 'title', 'message', 'metadata', 'created_at']


# ── Auth Serializers ─────────────────────────────────────────

class OTPRequestSerializer(serializers.Serializer):
    """Request an OTP via Supabase Auth."""
    phone = serializers.CharField(max_length=15)


class OTPVerifySerializer(serializers.Serializer):
    """Verify OTP and authenticate."""
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class RegisterSerializer(serializers.ModelSerializer):
    """Create a new user after OTP verification.

    Role is restricted to 'customer' during registration.
    Users who want to become operators must use the
    register_as_operator endpoint after creating a customer account.
    This ensures operators go through the verification flow.
    """

    class Meta:
        model = CustomUser
        fields = ['phone', 'name', 'email', 'role']
        extra_kwargs = {
            'role': {'required': False, 'default': 'customer'},
        }

    def validate_phone(self, value: str) -> str:
        """Ensure phone number is digits only and reasonable length."""
        cleaned = value.strip().lstrip('+')
        if not cleaned.isdigit():
            # Error Code: USR-SERIAL-VAL-001
            # Message: Phone contains non-digit characters
            # Cause: Phone number has letters or special characters
            # Solution: Provide digits-only phone number
            raise serializers.ValidationError(
                'Phone must contain only digits.',
                code='USR-SERIAL-VAL-001',
            )
        if len(cleaned) < 10 or len(cleaned) > 15:
            # Error Code: USR-SERIAL-VAL-002
            # Message: Phone number length invalid
            # Cause: Phone number is shorter than 10 or longer than 15 digits
            # Solution: Provide a phone number between 10-15 digits
            raise serializers.ValidationError(
                'Phone must be 10-15 digits.',
                code='USR-SERIAL-VAL-002',
            )
        return cleaned

    def validate_role(self, value: str) -> str:
        """Only customer role is allowed during registration.

        Operators must use the register_as_operator endpoint which
        collects business details and sets verification_status='pending'.
        This prevents unverified users from self-assigning operator role.
        """
        if value != CustomUser.Role.CUSTOMER.value:
            # Error Code: USR-SERIAL-VAL-003
            # Message: Registration role must be 'customer'
            # Cause: User tried to register as operator directly
            # Solution: Register as customer, then use register_as_operator endpoint
            raise serializers.ValidationError(
                "Register as customer first. Use the operator registration "
                "endpoint to become an operator.",
                code='USR-SERIAL-VAL-003',
            )
        return value
