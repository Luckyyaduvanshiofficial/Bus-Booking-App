"""Business logic for user management, auth, and documents.

All multi-step operations use @transaction.atomic.
Raises ValidationError for invalid data.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.users.models import CustomUser, Document, Notification

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client():
    """Return a cached Supabase client instance."""
    from supabase import create_client

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class AuthService:
    """Handles OTP-based authentication via Supabase."""

    @staticmethod
    def send_otp(*, phone: str) -> dict:
        """Send OTP to a phone number via Supabase Auth.

        Args:
            phone: Phone number to send OTP to.

        Returns:
            Dict with success message.

        Raises:
            ValidationError: If Supabase call fails.
        """
        try:
            supabase = get_supabase_client()
            supabase.auth.sign_in_with_otp({'phone': phone})
            return {'message': 'OTP sent successfully'}
        except Exception:
            # Error Code: USR-SERV-API-001
            # Message: Failed to send OTP
            # Cause: Supabase Auth API call failed
            # Solution: Check Supabase credentials, network, and Auth logs
            logger.error('Failed to send OTP', exc_info=True)
            raise ValidationError(
                'Failed to send OTP. Please try again later.',
                code='USR-SERV-API-001',
            )

    @staticmethod
    @transaction.atomic
    def verify_otp(*, phone: str, otp: str) -> dict:
        """Verify OTP and return/create Django user with auth token.

        Args:
            phone: Phone number to verify.
            otp: One-time password to verify.

        Returns:
            Dict with token, user, and is_new_user flag.

        Raises:
            ValidationError: If OTP verification fails.
        """
        try:
            from rest_framework.authtoken.models import Token

            supabase = get_supabase_client()
            resp = supabase.auth.verify_otp({
                'phone': phone, 'token': otp, 'type': 'sms',
            })

            if not resp.user:
                # Error Code: USR-SERV-AUTH-001
                # Message: Invalid phone/OTP combination
                # Cause: OTP verification failed via Supabase
                # Solution: Check Supabase Auth logs, request new OTP
                raise ValidationError(
                    'Invalid OTP.',
                    code='USR-SERV-AUTH-001',
                )

            user, created = CustomUser.objects.get_or_create(
                phone=phone,
                defaults={
                    'username': phone,
                    'supabase_uid': resp.user.id,
                },
            )
            if not created and not user.supabase_uid:
                user.supabase_uid = resp.user.id
                user.save(update_fields=['supabase_uid'])

            # Serialize token rotation per-user to avoid delete/create races
            # when OTP verification is submitted concurrently.
            user = CustomUser.objects.select_for_update().get(pk=user.pk)
            # Always mint a fresh token after successful OTP verification
            # to avoid returning a stale token that may already be expired.
            Token.objects.filter(user=user).delete()
            try:
                # Nested savepoint so IntegrityError doesn't break
                # the outer @transaction.atomic on PostgreSQL.
                with transaction.atomic():
                    token = Token.objects.create(user=user)
            except IntegrityError:
                # Concurrent verify request already created a fresh token.
                token = Token.objects.get(user=user)

            from .serializers import UserSerializer

            return {
                'token': token.key,
                'user': UserSerializer(user).data,
                'is_new_user': created,
            }
        except ValidationError:
            raise
        except Exception:
            # Error Code: USR-SERV-AUTH-002
            # Message: OTP verification failed unexpectedly
            # Cause: Supabase Auth error or network issue
            # Solution: Check Supabase status, retry OTP flow
            logger.error('Verification failed', exc_info=True)
            raise ValidationError(
                'Verification failed, please try again.',
                code='USR-SERV-AUTH-002',
            )

    @staticmethod
    @transaction.atomic
    def register_user(*, validated_data: dict) -> dict:
        """Register or update a user after OTP verification.

        Args:
            validated_data: Serializer-validated registration data.

        Returns:
            Dict with token, user, and created flag.
        """
        from rest_framework.authtoken.models import Token

        phone = validated_data['phone']
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={
                'username': phone,
                'name': validated_data.get('name', ''),
                'email': validated_data.get('email', ''),
                'role': validated_data.get('role', 'customer'),
            },
        )

        if not created:
            # Only update safe profile fields — NEVER allow role escalation.
            # An existing user re-registering should not be able to change
            # their role to 'admin' or 'operator' via this endpoint.
            for field in ('name', 'email'):
                val = validated_data.get(field)
                if val:
                    setattr(user, field, val)
            user.save()

        token, _ = Token.objects.get_or_create(user=user)

        from .serializers import UserSerializer

        return {
            'token': token.key,
            'user': UserSerializer(user).data,
            'created': created,
        }


class OperatorService:
    """Handles operator-specific operations."""

    @staticmethod
    @transaction.atomic
    def register_as_operator(
        *,
        user: CustomUser,
        validated_data: dict,
    ) -> CustomUser:
        """Convert a customer to operator role.

        Args:
            user: The user to convert.
            validated_data: Serializer-validated operator data.

        Returns:
            The updated user with operator role.

        Raises:
            ValidationError: If user is already an operator.
        """
        if user.role == 'operator':
            # Error Code: USR-SERV-CONFLICT-001
            # Message: User is already an operator
            # Cause: Attempting to re-register as operator
            # Solution: Check user.role before calling this endpoint
            raise ValidationError(
                'Already an operator.',
                code='USR-SERV-CONFLICT-001',
            )

        user.role = 'operator'
        user.verification_status = 'pending'
        for field, value in validated_data.items():
            setattr(user, field, value)
        user.full_clean()
        user.save()
        return user

    @staticmethod
    def get_dashboard(*, operator: CustomUser) -> dict:
        """Get operator dashboard summary.

        Uses a single aggregate query with conditional Count instead of
        three separate .filter().count() calls.

        Args:
            operator: The operator user.

        Returns:
            Dict with dashboard metrics.
        """
        from django.db.models import Count, Q
        from apps.bookings.models import Booking

        counts = Booking.objects.filter(operator=operator).aggregate(
            pending=Count('id', filter=Q(status='pending')),
            active=Count('id', filter=Q(status='confirmed')),
            completed=Count('id', filter=Q(status='completed')),
        )
        return {
            'total_buses': operator.total_buses,
            'total_bookings': operator.total_bookings,
            'rating_avg': float(operator.rating_avg) if operator.rating_avg is not None else None,
            'pending_bookings': counts['pending'],
            'active_bookings': counts['active'],
            'completed_bookings': counts['completed'],
        }


class DocumentService:
    """Handles document upload and verification."""

    @staticmethod
    @transaction.atomic
    def verify_document(
        *,
        document: Document,
        action: str,
        verified_by: CustomUser,
        rejection_reason: str = '',
    ) -> Document:
        """Admin approves or rejects a document.

        Args:
            document: The document to verify.
            action: 'approve' or 'reject'.
            verified_by: The admin performing verification.
            rejection_reason: Reason for rejection (if applicable).

        Returns:
            The updated Document instance.

        Raises:
            ValidationError: If action is invalid.
        """
        if action == 'approve':
            document.verification_status = 'verified'
        elif action == 'reject':
            document.verification_status = 'rejected'
            document.rejection_reason = rejection_reason
        else:
            # Error Code: DOC-SERV-VAL-001
            # Message: Invalid document verification action
            # Cause: action parameter is not 'approve' or 'reject'
            # Solution: Pass action='approve' or action='reject'
            raise ValidationError(
                'action must be approve or reject.',
                code='DOC-SERV-VAL-001',
            )

        document.verified_by = verified_by
        document.verified_at = timezone.now()
        document.save()
        return document


class UserService:
    """Handles user verification by admin."""

    @staticmethod
    @transaction.atomic
    def verify_user(
        *,
        user: CustomUser,
        action: str,
        reason: str = '',
    ) -> CustomUser:
        """Admin approves or rejects a user (operator).

        Args:
            user: The user to verify.
            action: 'approve' or 'reject'.
            reason: Rejection reason (if applicable).

        Returns:
            The updated user instance.

        Raises:
            ValidationError: If action is invalid.
        """
        if action == 'approve':
            user.is_verified = True
            user.verification_status = CustomUser.VerificationStatus.VERIFIED
            user.rejection_reason = ''
            user.verified_at = timezone.now()
            user.save(
                update_fields=[
                    'is_verified',
                    'verification_status',
                    'rejection_reason',
                    'verified_at',
                ],
            )
            Notification.objects.create(
                user=user,
                type=Notification.NotificationType.OPERATOR_VERIFIED,
                title='Operator Verification Approved',
                message='Your operator profile has been verified and activated.',
                metadata={'verification_status': 'verified'},
            )
        elif action == 'reject':
            user.is_verified = False
            user.verification_status = CustomUser.VerificationStatus.REJECTED
            user.rejection_reason = reason
            user.verified_at = None
            user.save(
                update_fields=[
                    'is_verified',
                    'verification_status',
                    'rejection_reason',
                    'verified_at',
                ],
            )
            Notification.objects.create(
                user=user,
                type=Notification.NotificationType.OPERATOR_REJECTED,
                title='Operator Verification Rejected',
                message=(
                    reason.strip()
                    if reason and reason.strip()
                    else 'Your operator verification was rejected. Please resubmit documents.'
                ),
                metadata={'verification_status': 'rejected'},
            )
        else:
            # Error Code: USR-SERV-VAL-001
            # Message: Invalid user verification action
            # Cause: action parameter is not 'approve' or 'reject'
            # Solution: Pass action='approve' or action='reject'
            raise ValidationError(
                'action must be approve or reject.',
                code='USR-SERV-VAL-001',
            )

        return user
