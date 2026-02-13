import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class BusReview(models.Model):
    """Bus review – PRD Section 4 (reviews table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    booking = models.OneToOneField(
        'bookings.Booking', on_delete=models.CASCADE, related_name='review',
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bus_reviews',
    )
    bus = models.ForeignKey(
        'buses.Bus', on_delete=models.CASCADE, related_name='reviews',
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='received_reviews',
    )

    # ── Ratings (1-5) ──
    rating_overall = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    rating_cleanliness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )
    rating_punctuality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )
    rating_driver = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )
    rating_value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
    )

    # ── Review text ──
    review_text = models.TextField(blank=True, null=True)

    # ── Photos ──
    photo_urls = models.JSONField(default=list, blank=True)

    # ── Admin moderation ──
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bus']),
            models.Index(fields=['operator']),
        ]

    def __str__(self):
        return f"Review by {self.customer} for {self.bus.name} ({self.rating_overall}★)"

    def save(self, *args, **kwargs):
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='operator_reviews',
        limit_choices_to={'role': 'operator'},
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='operator_reviews_given',
    )

    # Ratings
    responsiveness_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    professionalism_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    reliability_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    overall_rating = models.DecimalField(max_digits=2, decimal_places=1, editable=False)

    comment = models.TextField()
    is_approved = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'operator_reviews'
        ordering = ['-created_at']
        unique_together = ('operator', 'reviewer')

    def __str__(self):
        return f"Review by {self.reviewer} for {self.operator.business_name}"

    def save(self, *args, **kwargs):
        self.overall_rating = round(
            (self.responsiveness_rating + self.professionalism_rating + self.reliability_rating) / 3,
            1,
        )
        super().save(*args, **kwargs)
