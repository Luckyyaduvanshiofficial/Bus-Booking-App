"""Common utility functions with error codes from ERROR_REGISTRY.md.

Provides reusable validation helpers and configuration checkers.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_phone_format(phone: str) -> str:
    """Validate and normalize a phone number.

    Args:
        phone: The phone number to validate.

    Returns:
        Cleaned phone string.

    Raises:
        ValidationError (COM-UTILS-VAL-002): If phone format is invalid.
    """
    cleaned = phone.strip().lstrip('+')
    if not cleaned.isdigit() or len(cleaned) < 10 or len(cleaned) > 15:
        # Error Code: COM-UTILS-VAL-002
        # Message: Invalid phone number format
        # Cause: Phone validation failed
        # Solution: Use +91XXXXXXXXXX format
        raise ValidationError(
            'Invalid phone number format. Use +91XXXXXXXXXX.',
            code='COM-UTILS-VAL-002',
        )
    return cleaned


def validate_date_format(date_str: str) -> 'datetime.date':
    """Parse and validate a date string in YYYY-MM-DD format.

    Args:
        date_str: The date string to parse.

    Returns:
        A date object.

    Raises:
        ValidationError (COM-UTILS-VAL-001): If date format is invalid.
    """
    import datetime
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Error Code: COM-UTILS-VAL-001
        # Message: Invalid date format. Use YYYY-MM-DD
        # Cause: Date parsing error
        # Solution: Check date string format
        raise ValidationError(
            'Invalid date format. Use YYYY-MM-DD.',
            code='COM-UTILS-VAL-001',
        )


def require_env_var(var_name: str) -> str:
    """Get a required environment variable.

    Args:
        var_name: The name of the environment variable.

    Returns:
        The value of the environment variable.

    Raises:
        ValidationError (COM-UTILS-CONFIG-001): If the variable is not set.
    """
    import os
    value = os.environ.get(var_name, '')
    if not value:
        # Error Code: COM-UTILS-CONFIG-001
        # Message: Environment variable missing
        # Cause: Missing config
        # Solution: Set in .env file
        logger.error(
            'Missing environment variable: %s [COM-UTILS-CONFIG-001]',
            var_name,
        )
        raise ValidationError(
            f'Environment variable {var_name} is missing.',
            code='COM-UTILS-CONFIG-001',
        )
    return value


def upload_to_cloudinary(
    file_data,
    folder: str = 'bus_booking',
) -> str:
    """Upload a file to Cloudinary.

    Args:
        file_data: The file to upload.
        folder: Cloudinary folder path.

    Returns:
        The secure URL of the uploaded file.

    Raises:
        ValidationError (COM-UTILS-API-003): If upload fails.
    """
    try:
        import cloudinary.uploader
        result = cloudinary.uploader.upload(file_data, folder=folder)
        return result.get('secure_url', '')
    except Exception as e:
        # Error Code: COM-UTILS-API-003
        # Message: Cloudinary image upload failed
        # Cause: Storage error
        # Solution: Check quota, retry
        logger.error('Cloudinary upload failed', exc_info=True)
        raise ValidationError(
            'Image upload failed. Please try again.',
            code='COM-UTILS-API-003',
        )
