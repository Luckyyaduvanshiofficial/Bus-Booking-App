"""Celery tasks for notification system.

Handles async notification delivery via n8n → Brevo (WhatsApp + Email).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from celery import shared_task
from django.utils import timezone

if TYPE_CHECKING:
    from apps.users.models import Notification

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
)
def send_notification_via_n8n(
    self,
    notification_id: str,
    send_whatsapp: bool = False,
    send_email: bool = False,
) -> bool:
    """Send notification to n8n webhook for WhatsApp/Email delivery via Brevo.

    Args:
        notification_id: UUID of notification to send
        send_whatsapp: Whether to send WhatsApp
        send_email: Whether to send email

    Returns:
        bool: True if sent successfully

    Raises:
        Exception: If all retries fail
    """
    from apps.users.models import Notification
    from apps.common.notification_service import NotificationService

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(
            'Notification not found for n8n delivery',
            extra={'notification_id': notification_id}
        )
        return False

    try:
        success = NotificationService.trigger_n8n_webhook(
            notification=notification,
            send_whatsapp=send_whatsapp,
            send_email=send_email
        )
        
        if not success:
            # Retry task — raise a descriptive exception for Celery logs
            raise self.retry(
                exc=RuntimeError('n8n webhook returned failure'),
            )

        return True

    except Exception as e:
        logger.error(
            'Error sending notification via n8n',
            extra={
                'notification_id': notification_id,
                'error': str(e),
                'retry_count': self.request.retries
            }
        )
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return False


@shared_task
def send_trip_reminders() -> dict:
    """Send trip reminders 6 hours before pickup time via WhatsApp.

    Runs every hour via Celery Beat.
    Sends WhatsApp reminders to customers with confirmed bookings.

    Returns:
        dict: Stats about reminders sent
    """
    from apps.bookings.models import Booking
    from apps.common.notification_service import NotificationService

    logger.info('Starting trip reminder task')

    # Find bookings with pickup in next 6 hours
    now = timezone.now()
    reminder_window_start = now + timedelta(hours=5, minutes=30)
    reminder_window_end = now + timedelta(hours=6, minutes=30)

    bookings = Booking.objects.filter(
        status='confirmed',
        pickup_date__gte=now.date(),
        pickup_date__lte=(now + timedelta(days=1)).date(),
        metadata__reminder_sent__isnull=True  # Not sent yet
    ).select_related('customer', 'bus', 'operator')

    sent_count = 0
    failed_count = 0

    for booking in bookings:
        try:
            # Combine pickup date and time
            from datetime import datetime
            pickup_datetime = datetime.combine(
                booking.pickup_date,
                booking.pickup_time
            )
            pickup_datetime = timezone.make_aware(
                pickup_datetime,
                timezone=timezone.get_current_timezone(),
            )

            # Check if within reminder window
            if not (reminder_window_start <= pickup_datetime <= reminder_window_end):
                continue

            # Send reminder to customer via WhatsApp
            message = (
                f"🚌 Trip Reminder: Your bus journey starts in 6 hours!\n\n"
                f"📋 Booking: {booking.booking_number}\n"
                f"🚍 Bus: {booking.bus.name}\n"
                f"📍 Pickup: {booking.pickup_location}\n"
                f"🕒 Time: {booking.pickup_time.strftime('%I:%M %p')}\n"
                f"📞 Operator: {booking.bus.operator.phone}\n\n"
                f"Have a safe journey!"
            )

            NotificationService.create_notification(
                user=booking.customer,
                notification_type='trip_reminder',
                title=f'Trip Reminder - {booking.booking_number}',
                message=message,
                metadata={
                    'booking_id': str(booking.id),
                    'pickup_datetime': pickup_datetime.isoformat()
                },
                send_whatsapp=True,
                send_email=False  # WhatsApp only for reminders
            )

            # Mark reminder as sent
            booking.metadata = booking.metadata or {}
            booking.metadata['reminder_sent'] = True
            booking.metadata['reminder_sent_at'] = now.isoformat()
            booking.save(update_fields=['metadata'])

            sent_count += 1

            logger.info(
                'Trip reminder sent',
                extra={
                    'booking_id': str(booking.id),
                    'customer_id': str(booking.customer.id)
                }
            )

        except Exception as e:
            failed_count += 1
            logger.error(
                'Failed to send trip reminder',
                extra={
                    'booking_id': str(booking.id),
                    'error': str(e)
                }
            )

    stats = {
        'sent_count': sent_count,
        'failed_count': failed_count,
        'total_checked': bookings.count()
    }

    logger.info(
        'Trip reminder task completed',
        extra=stats
    )

    return stats


@shared_task
def cleanup_old_notifications() -> dict:
    """Delete read notifications older than 90 days.

    Runs daily via Celery Beat to keep database clean.

    Returns:
        dict: Stats about deletions
    """
    from apps.users.models import Notification

    logger.info('Starting notification cleanup task')

    cutoff_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()

    stats = {
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }

    logger.info(
        'Notification cleanup completed',
        extra=stats
    )

    return stats
