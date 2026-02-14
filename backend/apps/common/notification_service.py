"""Notification service for WhatsApp and Email via n8n → Brevo.

Handles notification creation, n8n webhook triggers, and delivery tracking.
Follows FAANG-level standards from Copilot Instructions.

Brevo Integration:
- WhatsApp marketing via Brevo Conversations API
- Transactional emails via Brevo SMTP API
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from apps.users.models import CustomUser, Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and sending notifications via n8n webhooks."""

    @staticmethod
    def create_notification(
        *,
        user: CustomUser,
        notification_type: str,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
        send_whatsapp: bool = False,
        send_email: bool = False,
    ) -> Notification:
        """Create a notification record in database.

        Args:
            user: User to notify
            notification_type: Type from Notification.NotificationType choices
            title: Notification title (max 200 chars)
            message: Notification message body
            metadata: Additional data (booking_id, payment_id, etc.)
            send_whatsapp: Whether to send WhatsApp via Brevo
            send_email: Whether to send email via Brevo

        Returns:
            Notification: Created notification instance

        Raises:
            ValidationError: If validation fails (code: NOT-SERV-VAL-XXX)

        Example:
            >>> NotificationService.create_notification(
            ...     user=customer,
            ...     notification_type='booking_confirmed',
            ...     title='Booking Confirmed',
            ...     message='Your booking #BK-123 has been confirmed',
            ...     metadata={'booking_id': str(booking.id)},
            ...     send_whatsapp=True,
            ...     send_email=True
            ... )
        """
        from apps.users.models import Notification

        # Error Code: NOT-SERV-VAL-001
        # Message: User must be active to receive notifications
        # Cause: Attempting to notify inactive user
        # Solution: Verify user.is_active before calling
        if not user.is_active:
            logger.warning(
                'Notification to inactive user blocked',
                extra={'user_id': str(user.id), 'type': notification_type}
            )
            raise ValidationError(
                'Cannot send notification to inactive user',
                code='NOT-SERV-VAL-001'
            )

        # Error Code: NOT-SERV-VAL-002
        # Message: Notification type is invalid
        # Cause: notification_type not in Notification.NotificationType choices
        # Solution: Use valid type from Notification.NotificationType
        valid_types = [choice[0] for choice in Notification.NotificationType.choices]
        if notification_type not in valid_types:
            raise ValidationError(
                f'Invalid notification type: {notification_type}',
                code='NOT-SERV-VAL-002'
            )

        # Create notification record
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {},
        )

        logger.info(
            'Notification created',
            extra={
                'notification_id': str(notification.id),
                'user_id': str(user.id),
                'type': notification_type
            }
        )

        # Trigger WhatsApp/Email via n8n → Brevo (async)
        if send_whatsapp or send_email:
            from apps.common.tasks import send_notification_via_n8n
            send_notification_via_n8n.delay(
                notification_id=str(notification.id),
                send_whatsapp=send_whatsapp,
                send_email=send_email
            )

        return notification

    @staticmethod
    def trigger_n8n_webhook(
        *,
        notification: Notification,
        send_whatsapp: bool = False,
        send_email: bool = False,
    ) -> bool:
        """Send notification to n8n webhook for WhatsApp/Email delivery via Brevo.

        Args:
            notification: Notification instance to send
            send_whatsapp: Whether to trigger WhatsApp via Brevo
            send_email: Whether to trigger email via Brevo

        Returns:
            bool: True if webhook call succeeded, False otherwise

        Raises:
            ValidationError: If n8n webhook configuration missing (code: NOT-SERV-CONF-001)

        Example:
            >>> NotificationService.trigger_n8n_webhook(
            ...     notification=notification,
            ...     send_whatsapp=True,
            ...     send_email=True
            ... )
        """
        # Error Code: NOT-SERV-CONF-001
        # Message: N8N_WEBHOOK_URL not configured
        # Cause: Missing N8N_WEBHOOK_URL in settings
        # Solution: Set N8N_WEBHOOK_URL environment variable
        webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
        if not webhook_url:
            logger.error(
                'N8N_WEBHOOK_URL not configured',
                extra={'notification_id': str(notification.id)}
            )
            raise ValidationError(
                'N8N webhook URL not configured in settings',
                code='NOT-SERV-CONF-001'
            )

        user = notification.user

        # Prepare webhook payload for Brevo delivery
        payload = {
            'event': notification.type,
            'notification_id': str(notification.id),
            'user_id': str(user.id),
            'title': notification.title,
            'message': notification.message,
            'metadata': notification.metadata,
            'channels': {
                'whatsapp': send_whatsapp,
                'email': send_email,
            },
            'recipients': {
                'phone': user.phone if send_whatsapp else None,
                'email': user.email if send_email else None,
                'name': user.name or user.get_full_name(),
            },
            'timestamp': timezone.now().isoformat(),
        }

        # Call n8n webhook with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201, 202]:
                    # Update notification delivery status
                    if send_whatsapp:
                        notification.whatsapp_sent = True
                        notification.whatsapp_sent_at = timezone.now()
                    if send_email:
                        notification.email_sent = True
                        notification.email_sent_at = timezone.now()
                    
                    notification.save(update_fields=[
                        'whatsapp_sent', 'whatsapp_sent_at',
                        'email_sent', 'email_sent_at'
                    ])

                    logger.info(
                        'n8n webhook delivered',
                        extra={
                            'notification_id': str(notification.id),
                            'whatsapp': send_whatsapp,
                            'email': send_email,
                            'attempt': attempt + 1
                        }
                    )
                    return True
                else:
                    # Error Code: NOT-SERV-API-001
                    # Message: n8n webhook returned non-2xx status
                    # Cause: n8n returned error or is down
                    # Solution: Check n8n workflow and logs
                    logger.warning(
                        'n8n webhook returned error',
                        extra={
                            'notification_id': str(notification.id),
                            'status_code': response.status_code,
                            'response': response.text[:500],
                            'attempt': attempt + 1
                        }
                    )
                    
            except requests.exceptions.Timeout:
                logger.warning(
                    'n8n webhook timeout',
                    extra={
                        'notification_id': str(notification.id),
                        'attempt': attempt + 1
                    }
                )
                
            except requests.exceptions.RequestException as e:
                logger.error(
                    'n8n webhook request failed',
                    extra={
                        'notification_id': str(notification.id),
                        'error': str(e),
                        'attempt': attempt + 1
                    }
                )

            # Exponential backoff
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # 1s, 2s, 4s

        # All retries failed
        # Error Code: NOT-SERV-API-002
        # Message: n8n webhook failed after retries
        # Cause: Network error or n8n down
        # Solution: Check network and n8n availability
        logger.error(
            'n8n webhook failed after retries',
            extra={
                'notification_id': str(notification.id),
                'max_retries': max_retries
            }
        )
        return False

    @staticmethod
    def mark_as_read(*, notification: Notification) -> Notification:
        """Mark notification as read.

        Args:
            notification: Notification to mark as read

        Returns:
            Notification: Updated notification

        Example:
            >>> NotificationService.mark_as_read(notification=notification)
        """
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])

            logger.info(
                'Notification marked as read',
                extra={'notification_id': str(notification.id)}
            )

        return notification

    @staticmethod
    def get_unread_count(*, user: CustomUser) -> int:
        """Get count of unread notifications for user.

        Args:
            user: User to count unread notifications for

        Returns:
            int: Count of unread notifications

        Example:
            >>> count = NotificationService.get_unread_count(user=request.user)
        """
        from apps.users.models import Notification
        
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
