"""Custom exception handler with error code support.

Provides consistent error response format across the platform.
"""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Handle exceptions consistently with error codes.

    Ensures all error responses include a 'code' field matching
    ERROR_REGISTRY.md format.
    """
    # Call DRF default handler first
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, NotAuthenticated):
            # Error Code: USR-VIEWS-AUTH-001
            # Message: Authentication required
            # Cause: No auth token provided
            # Solution: Check Authorization header
            response.data = {
                'error': 'Authentication required.',
                'code': 'USR-VIEWS-AUTH-001',
            }

        elif isinstance(exc, AuthenticationFailed):
            code = getattr(exc, 'code', None)
            if isinstance(code, str) and '-' in code:
                # Preserve explicit auth codes from custom auth backends
                # such as USR-VIEWS-AUTH-003 for expired tokens.
                response.data = {
                    'error': str(exc.detail),
                    'code': code,
                }
            else:
                # Error Code: USR-VIEWS-AUTH-002
                # Message: Invalid or expired token
                # Cause: Token is malformed/expired
                # Solution: Re-login to get new token
                response.data = {
                    'error': 'Invalid or expired token.',
                    'code': 'USR-VIEWS-AUTH-002',
                }

        elif isinstance(exc, PermissionDenied):
            code = getattr(exc, 'code', 'permission_denied')
            if isinstance(code, str) and '-' in code:
                # Already has a proper error code
                response.data = {
                    'error': str(exc.detail),
                    'code': code,
                }

    elif isinstance(exc, DjangoValidationError):
        # Handle Django ValidationError (from model clean())
        # Supports single message, list of messages, and dict of field errors
        code = getattr(exc, 'code', 'validation_error')
        if hasattr(exc, 'message_dict'):
            # Field-specific errors: {'field': ['error1', 'error2']}
            error_detail = exc.message_dict
        elif hasattr(exc, 'messages'):
            # List of messages
            error_detail = exc.messages
        else:
            error_detail = str(getattr(exc, 'message', str(exc)))
        response = Response(
            {'error': error_detail, 'code': code},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return response
