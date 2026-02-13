"""Review models – PRD Section 4.

BusReview and OperatorReview models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class BusReview(models.Model):
    """Bus review – PRD Section 4 (reviews table)."""

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    booking: 'Booking' = models.OneToOneField(
        'bookings.Booking', on_delete=models.CASCADE,
        related_name='review', db_index=True,
    )
    customer: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bus_reviews', db_index=True,
    )
    bus: 'Bus' = models.ForeignKey(
        'buses.Bus', on_delete=models.CASCADE,
        related_name='reviews',
    )
    operator: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='received_reviews',
    )

    # ── Ratings (1-5) ──
    rating_overall: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    rating_cleanliness: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )
    rating_punctuality: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )
    rating_driver: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )
    rating_value: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )

    # ── Review text ──
    review_text: str = models.TextField(blank=True, null=True)

    # ── Photos ──
    photo_urls: list = models.JSONField(default=list, blank=True)

    # ── Admin moderation ──
    is_approved: bool = models.BooleanField(default=True)
    is_flagged: bool = models.BooleanField(default=False)

    created_at: datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bus']),
            models.Index(fields=['operator']),
        ]

    def __str__(self) -> str:
        return f"Review by {self.customer} for {self.bus.name} ({self.rating_overall}★)"

    def clean(self) -> None:
        """Model-level validation with error codes from ERROR_REGISTRY.md."""
        super().clean()
        from django.core.exceptions import ValidationError

        # Error Code: REV-MODELS-VAL-001
        # Message: Rating must be between 1 and 5
        # Cause: Invalid rating value
        # Solution: Check rating field validation
        if self.rating_overall is not None and not (1 <= self.rating_overall <= 5):
            raise ValidationError(
                'Rating must be between 1 and 5.',
                code='REV-MODELS-VAL-001',
            )

        # Error Code: REV-MODELS-VAL-002
        # Message: Review comment required (min 10 characters)
        # Cause: Too short comment
        # Solution: Write meaningful review
        if self.review_text and len(self.review_text.strip()) < 10:
            raise ValidationError(
                'Review text must be at least 10 characters.',
                code='REV-MODELS-VAL-002',
            )

        # Error Code: REV-MODELS-CONFLICT-001
        # Message: Cannot review booking before completion
        # Cause: Early review attempt
        # Solution: Wait until trip ends
        if (self.booking_id and hasattr(self, 'booking') and self.booking
                and self.booking.status != 'completed'):
            raise ValidationError(
                'Only completed bookings can be reviewed.',
                code='REV-MODELS-CONFLICT-001',
            )

    def save(self, *args, validate: bool = False, **kwargs) -> None:
        """Optionally validate, save, and update bus/operator ratings.

        Args:
            validate: If True, run full_clean() before saving. Defaults to
                False to avoid breaking bulk/partial operations.
        """
        if validate:
            self.full_clean()
        super().save(*args, **kwargs)
        self._update_bus_ratings()
        self._update_operator_ratings()

    def _update_bus_ratings(self):
        """Recalculate bus average rating and count."""
        reviews = BusReview.objects.filter(bus=self.bus, is_approved=True)
        if reviews.exists():
            from django.db.models import Avg
            avg = reviews.aggregate(avg=Avg('rating_overall'))['avg']
            self.bus.rating_avg = round(avg, 1)
            self.bus.rating_count = reviews.count()
            self.bus.save(update_fields=['rating_avg', 'rating_count'])

    def _update_operator_ratings(self):
        """Recalculate operator average rating and count."""
        reviews = BusReview.objects.filter(operator=self.operator, is_approved=True)
        if reviews.exists():
            from django.db.models import Avg
            avg = reviews.aggregate(avg=Avg('rating_overall'))['avg']
            self.operator.rating_avg = round(avg, 1)
            self.operator.rating_count = reviews.count()
            self.operator.save(update_fields=['rating_avg', 'rating_count'])


class OperatorReview(models.Model):
    """Reviews for operators (separate from bus reviews)."""

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )

    operator: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='operator_reviews', db_index=True,
        limit_choices_to={'role': 'operator'},
    )
    reviewer: 'CustomUser' = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='operator_reviews_given', db_index=True,
    )

    # Ratings
    responsiveness_rating: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    professionalism_rating: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    reliability_rating: int = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    overall_rating: models.DecimalField = models.DecimalField(
        max_digits=2, decimal_places=1, editable=False,
    )

    comment: str = models.TextField()
    is_approved: bool = models.BooleanField(default=True)

    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'operator_reviews'
        ordering = ['-created_at']
        unique_together = ('operator', 'reviewer')

    def __str__(self) -> str:
        return f"Review by {self.reviewer} for {self.operator.business_name}"

    def save(self, *args, **kwargs) -> None:
        """Calculate overall rating, validate, and save."""
        self.overall_rating = round(
            (self.responsiveness_rating + self.professionalism_rating + self.reliability_rating) / 3,
            1,
        )
        self.full_clean()
        super().save(*args, **kwargs)
