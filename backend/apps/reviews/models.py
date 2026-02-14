"""Review models – PRD Section 4.

BusReview and OperatorReview models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.apps import apps
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Avg, Count


def _recalculate_operator_rating(operator_id) -> None:
    """Recompute operator rating using approved bus + operator reviews."""
    user_model = apps.get_model('users', 'CustomUser')
    with transaction.atomic():
        operator = user_model.objects.select_for_update().get(pk=operator_id)

        bus_aggregates = BusReview.objects.filter(
            operator_id=operator_id,
            is_approved=True,
        ).aggregate(
            avg=Avg('rating_overall'),
            count=Count('id'),
        )
        operator_aggregates = OperatorReview.objects.filter(
            operator_id=operator_id,
            is_approved=True,
        ).aggregate(
            avg=Avg('overall_rating'),
            count=Count('id'),
        )

        bus_count = int(bus_aggregates['count'] or 0)
        op_count = int(operator_aggregates['count'] or 0)
        total_count = bus_count + op_count

        if total_count == 0:
            operator.rating_avg = Decimal('0.0')
            operator.rating_count = 0
            operator.save(update_fields=['rating_avg', 'rating_count'])
            return

        bus_sum = Decimal(str(bus_aggregates['avg'] or 0)) * bus_count
        op_sum = Decimal(str(operator_aggregates['avg'] or 0)) * op_count
        weighted_avg = ((bus_sum + op_sum) / Decimal(total_count)).quantize(
            Decimal('0.1'),
            rounding=ROUND_HALF_UP,
        )
        operator.rating_avg = weighted_avg
        operator.rating_count = total_count
        operator.save(update_fields=['rating_avg', 'rating_count'])


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

    def save(self, *args, **kwargs) -> None:
        """Always validate before saving.

        Only recalculate bus/operator ratings when:
        - Creating a new review (no pk yet)
        - The is_approved flag has changed (admin moderation)
        This avoids 4 extra queries on every save (e.g., flagging).
        """
        is_new = self.pk is None
        approval_changed = False
        if not is_new:
            try:
                old = BusReview.objects.only('is_approved').get(pk=self.pk)
                approval_changed = old.is_approved != self.is_approved
            except BusReview.DoesNotExist:
                is_new = True

        self.full_clean()
        super().save(*args, **kwargs)

        if is_new or approval_changed:
            self._update_bus_ratings()
            self._update_operator_ratings()

    def _update_bus_ratings(self):
        """Recalculate bus average rating and count under row lock."""
        bus_model = type(self.bus)
        with transaction.atomic():
            bus = bus_model.objects.select_for_update().get(pk=self.bus_id)
            aggregates = BusReview.objects.filter(
                bus_id=self.bus_id,
                is_approved=True,
            ).aggregate(
                avg=Avg('rating_overall'),
                count=Count('id'),
            )
            bus.rating_avg = round(aggregates['avg'] or 0, 1)
            bus.rating_count = aggregates['count'] or 0
            bus.save(update_fields=['rating_avg', 'rating_count'])

    def _update_operator_ratings(self):
        """Recalculate operator average rating and count under row lock."""
        _recalculate_operator_rating(self.operator_id)


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
        """Calculate overall rating, validate, and save.

        Only recalculate operator aggregate when:
        - Creating a new approved review
        - The is_approved flag changed (admin moderation)
        - An approved review's computed overall_rating changed
        This avoids unnecessary aggregate queries on unrelated edits.
        """
        is_new = self.pk is None
        approval_changed = False
        old_overall = None
        if not is_new:
            try:
                old = OperatorReview.objects.only(
                    'is_approved', 'overall_rating',
                ).get(pk=self.pk)
                approval_changed = old.is_approved != self.is_approved
                old_overall = old.overall_rating
            except OperatorReview.DoesNotExist:
                is_new = True

        total_score = (
            self.responsiveness_rating
            + self.professionalism_rating
            + self.reliability_rating
        )
        self.overall_rating = (
            Decimal(total_score) / Decimal('3')
        ).quantize(
            Decimal('0.1'),
            rounding=ROUND_HALF_UP,
        )

        rating_changed = (
            old_overall is not None and old_overall != self.overall_rating
        )

        self.full_clean()
        super().save(*args, **kwargs)

        if (
            (is_new and self.is_approved)
            or approval_changed
            or (self.is_approved and rating_changed)
        ):
            _recalculate_operator_rating(self.operator_id)
