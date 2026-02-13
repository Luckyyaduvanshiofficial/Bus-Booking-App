"""Expiring token authentication.

DRF's default TokenAuthentication creates permanent tokens. For a
payment-handling platform, tokens should expire after a configurable
duration (default: 7 days).

Usage:
    Set in settings.py REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']:
        'apps.common.authentication.ExpiringTokenAuthentication'

    Configure TTL in settings.py:
        TOKEN_EXPIRY_HOURS = 168  # 7 days
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

# Default: 7 days (168 hours)
TOKEN_EXPIRY_HOURS: int = getattr(settings, 'TOKEN_EXPIRY_HOURS', 168)


class ExpiringTokenAuthentication(TokenAuthentication):
    """Token authentication with automatic expiry.

    If the token is older than TOKEN_EXPIRY_HOURS, it is deleted and
    the user must re-authenticate via OTP to get a fresh token.

    Error Codes:
        USR-VIEWS-AUTH-003: Token expired — re-login required
    """

    def authenticate_credentials(self, key: str):
        """Validate token and check expiry.

        Args:
            key: The raw token string from the Authorization header.

        Returns:
            Tuple of (user, token) if valid.

        Raises:
            AuthenticationFailed: If token is invalid or expired.
        """
        user, token = super().authenticate_credentials(key)

        expiry_threshold = timezone.now() - timedelta(hours=TOKEN_EXPIRY_HOURS)
        if token.created < expiry_threshold:
            # Token has expired — delete it and force re-authentication
            token.delete()
            # Error Code: USR-VIEWS-AUTH-003
            # Message: Token expired
            # Cause: Token is older than TOKEN_EXPIRY_HOURS
            # Solution: Re-login via OTP to get a fresh token
            logger.info(
                'Token expired for user %s [USR-VIEWS-AUTH-003]',
                user.id,
            )
            raise AuthenticationFailed(
                'Token has expired. Please log in again.',
                code='USR-VIEWS-AUTH-003',
            )

        return user, token
