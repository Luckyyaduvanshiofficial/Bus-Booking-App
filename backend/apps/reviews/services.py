"""Business logic for review management.

Raises ValidationError for invalid data.
"""

from __future__ import annotations

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.reviews.models import BusReview, OperatorReview


class ReviewService:
    """Handles review moderation."""

    @staticmethod
    @transaction.atomic
    def moderate_review(
        *,
        review: BusReview,
        action: str,
    ) -> BusReview:
        """Admin moderates a bus review.

        Args:
            review: The review to moderate.
            action: 'approve', 'flag', or 'remove'.

        Returns:
            The updated BusReview instance.

        Raises:
            ValidationError: If action is invalid.
        """
        if action == 'approve':
            review.is_approved = True
            review.is_flagged = False
            update_fields = ['is_approved', 'is_flagged']
        elif action == 'flag':
            review.is_flagged = True
            update_fields = ['is_flagged']
        elif action == 'remove':
            review.is_approved = False
            update_fields = ['is_approved']
        else:
            # Error Code: REV-SERV-VAL-001
            # Message: Invalid review moderation action
            # Cause: action parameter is not 'approve', 'flag', or 'remove'
            # Solution: Pass action='approve', 'flag', or 'remove'
            raise ValidationError(
                'action must be approve, flag, or remove.',
                code='REV-SERV-VAL-001',
            )

        review.save(update_fields=update_fields)
        return review
