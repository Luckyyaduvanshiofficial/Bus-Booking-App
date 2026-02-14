# Notification System Documentation

## Overview

The notification system sends SMS and email notifications to users via n8n webhooks. It includes:
- In-app notification records in database
- SMS delivery via n8n → Twilio/MSG91
- Email delivery via n8n → SendGrid/SMTP
- Celery tasks for async delivery
- Retry logic with exponential backoff
- Trip reminders 6 hours before pickup

## Quick Start

### 1. Configuration
```bash
# Add to .env
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/notifications
```

### 2. Usage Example
```python
from apps.common.notification_service import NotificationService

NotificationService.create_notification(
    user=booking.customer,
    notification_type='booking_confirmed',
    title=f'Booking Confirmed - {booking.booking_number}',
    message='Your booking has been confirmed...',
    metadata={'booking_id': str(booking.id)},
    send_sms=True,
    send_email=True
)
```

### 3. n8n Webhook Payload
```json
{
  "event": "booking_confirmed",
  "notification_id": "uuid",
  "channels": {"sms": true, "email": true},
  "recipients": {
    "phone": "+919876543210",
    "email": "customer@example.com"
  },
  "title": "Booking Confirmed",
  "message": "Your booking has been confirmed..."
}
```

## Notification Types

- `booking_created` - New booking request created (SMS to customer + operator)
- `booking_confirmed` - Operator accepted booking (SMS + Email to customer)
- `booking_rejected` - Operator rejected booking (SMS + Email to customer)
- `booking_cancelled` - Booking cancelled (SMS + Email)
- `trip_reminder` - 6h before pickup (SMS only)
- `payment_received` - Payment confirmed (Email only)

## API Endpoints

- `GET /api/v1/notifications/` - List notifications
- `POST /api/v1/notifications/{id}/mark_read/` - Mark as read
- `POST /api/v1/notifications/mark_all_read/` - Mark all as read
- `GET /api/v1/notifications/unread_count/` - Get unread count

## Celery Tasks

- `send_notification_via_n8n` - Async delivery (3 retries, exponential backoff)
- `send_trip_reminders` - Runs hourly, sends 6h before pickup
- `cleanup_old_notifications` - Runs daily, deletes read notifications > 90 days

## Testing

```bash
# Run tests
python manage.py test apps.common.tests_notifications

# Manual test
python manage.py shell
>>> from apps.common.notification_service import NotificationService
>>> from apps.users.models import CustomUser
>>> user = CustomUser.objects.first()
>>> NotificationService.create_notification(
...     user=user,
...     notification_type='booking_confirmed',
...     title='Test',
...     message='Test message',
...     send_sms=True
... )
```

## Error Codes

- `NOT-SERV-VAL-001` - User must be active
- `NOT-SERV-VAL-002` - Invalid notification type
- `NOT-SERV-CONF-001` - N8N_WEBHOOK_URL not configured
- `NOT-SERV-API-001` - n8n webhook error
- `NOT-SERV-API-002` - n8n webhook failed after retries

For full documentation, see detailed architecture and n8n setup guide in project wiki.
