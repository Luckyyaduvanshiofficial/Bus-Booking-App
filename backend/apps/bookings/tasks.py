"""Background tasks for bookings app."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.bookings.models import Booking, BookingHistory, Payment
from apps.bookings.services import PaymentService
from apps.buses.models import AvailabilityBlock

logger = logging.getLogger(__name__)


def _expire_single_pending_booking(
    *,
    booking_id,
    cutoff,
    expiry_hours: int,
) -> bool:
    """Expire one pending booking in an isolated transaction."""
    with transaction.atomic():
        booking = Booking.objects.select_for_update().filter(
            pk=booking_id,
            status=Booking.Status.PENDING,
            created_at__lte=cutoff,
        ).first()
        if booking is None:
            return False

        old_status = booking.status
        captured_total = Payment.objects.filter(
            booking=booking,
            status=Payment.CfStatus.CAPTURED,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        refund_amount = booking.calculate_refund() if captured_total else Decimal('0.00')
        if captured_total and refund_amount > captured_total:
            refund_amount = captured_total

        booking.status = Booking.Status.EXPIRED
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = (
            f'Auto-expired after {expiry_hours} hours without operator response/payment.'
        )
        booking.refund_amount = refund_amount
        update_fields = [
            'status',
            'cancelled_at',
            'cancellation_reason',
            'refund_amount',
        ]
        booking.save(update_fields=update_fields)

        AvailabilityBlock.objects.filter(booking=booking).delete()
        BookingHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=Booking.Status.EXPIRED,
            reason='Pending booking auto-expired',
            created_by=None,
        )
        if refund_amount > Decimal('0.00'):
            PaymentService.schedule_booking_refund_post_commit(
                booking_id=booking.id,
                amount=refund_amount,
                reason='Auto-expired pending booking',
            )
        return True


@shared_task
def expire_pending_bookings() -> int:
    """Expire stale pending bookings and release blocked dates.

    Returns:
        Number of bookings expired in this run.
    """
    expiry_hours = max(int(getattr(settings, 'PENDING_BOOKING_EXPIRY_HOURS', 24)), 1)
    cutoff = timezone.now() - timedelta(hours=expiry_hours)
    stale_booking_ids = list(
        Booking.objects.filter(
            status=Booking.Status.PENDING,
            created_at__lte=cutoff,
        ).values_list('id', flat=True),
    )
    expired_count = 0
    for booking_id in stale_booking_ids:
        try:
            if _expire_single_pending_booking(
                booking_id=booking_id,
                cutoff=cutoff,
                expiry_hours=expiry_hours,
            ):
                expired_count += 1
        except Exception:
            logger.exception(
                'Failed to auto-expire booking %s; continuing with remaining rows.',
                booking_id,
            )
    return expired_count
