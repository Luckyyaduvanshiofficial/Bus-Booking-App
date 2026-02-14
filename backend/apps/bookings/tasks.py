"""Background tasks for bookings app."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking, BookingHistory
from apps.buses.models import AvailabilityBlock


@shared_task
def expire_pending_bookings() -> int:
    """Expire stale pending bookings and release blocked dates.

    Returns:
        Number of bookings expired in this run.
    """
    expiry_hours = max(int(getattr(settings, 'PENDING_BOOKING_EXPIRY_HOURS', 24)), 1)
    cutoff = timezone.now() - timedelta(hours=expiry_hours)
    expired_count = 0

    with transaction.atomic():
        stale_bookings = list(
            Booking.objects.select_for_update().filter(
                status=Booking.Status.PENDING,
                created_at__lte=cutoff,
            ),
        )
        if not stale_bookings:
            return 0

        now = timezone.now()
        for booking in stale_bookings:
            old_status = booking.status
            booking.status = Booking.Status.EXPIRED
            booking.cancelled_at = now
            booking.cancellation_reason = (
                f'Auto-expired after {expiry_hours} hours without operator response/payment.'
            )
            booking.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])

            AvailabilityBlock.objects.filter(booking=booking).delete()
            BookingHistory.objects.create(
                booking=booking,
                old_status=old_status,
                new_status=Booking.Status.EXPIRED,
                reason='Pending booking auto-expired',
                created_by=None,
            )
            expired_count += 1

    return expired_count
