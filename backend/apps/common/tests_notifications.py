"""Tests for notification system.

Tests NotificationService, n8n webhook integration, and Celery tasks.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.bookings.models import Booking
from apps.buses.models import Bus
from apps.common.notification_service import NotificationService
from apps.common.tasks import send_notification_via_n8n, send_trip_reminders
from apps.users.models import CustomUser, Notification


class NotificationServiceTest(TestCase):
    """Test NotificationService business logic."""

    def setUp(self):
        """Create test users."""
        self.customer = CustomUser(
            phone='+919876543210',
            username='+919876543210',
            name='Test Customer',
            role='customer',
            is_active=True,
        )
        self.customer.save(skip_validation=True)

        self.operator = CustomUser(
            phone='+919876543211',
            username='+919876543211',
            name='Test Operator',
            role='operator',
            is_verified=True,
            is_active=True,
        )
        self.operator.save(skip_validation=True)

    def test_create_notification_success(self):
        """Creating notification records it in database."""
        notification = NotificationService.create_notification(
            user=self.customer,
            notification_type='booking_created',
            title='Test Notification',
            message='This is a test message',
            metadata={'test_key': 'test_value'},
            send_sms=False,
            send_email=False
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.user, self.customer)
        self.assertEqual(notification.type, 'booking_created')
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test message')
        self.assertEqual(notification.metadata, {'test_key': 'test_value'})
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.sms_sent)
        self.assertFalse(notification.email_sent)

    def test_create_notification_inactive_user_fails(self):
        """Cannot create notification for inactive user."""
        self.customer.is_active = False
        self.customer.save(skip_validation=True)

        with self.assertRaises(ValidationError) as ctx:
            NotificationService.create_notification(
                user=self.customer,
                notification_type='booking_created',
                title='Test',
                message='Test',
            )
        
        self.assertIn('NOT-SERV-VAL-001', str(ctx.exception))

    def test_create_notification_invalid_type_fails(self):
        """Cannot create notification with invalid type."""
        with self.assertRaises(ValidationError) as ctx:
            NotificationService.create_notification(
                user=self.customer,
                notification_type='invalid_type',
                title='Test',
                message='Test',
            )
        
        self.assertIn('NOT-SERV-VAL-002', str(ctx.exception))

    @patch('apps.common.notification_service.requests.post')
    @override_settings(N8N_WEBHOOK_URL='https://n8n.example.com/webhook')
    def test_trigger_n8n_webhook_success(self, mock_post):
        """Successful n8n webhook call marks notification as sent."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notification = Notification.objects.create(
            user=self.customer,
            type='booking_confirmed',
            title='Test',
            message='Test message',
        )

        success = NotificationService.trigger_n8n_webhook(
            notification=notification,
            send_sms=True,
            send_email=True
        )

        self.assertTrue(success)
        
        # Refresh from DB
        notification.refresh_from_db()
        self.assertTrue(notification.sms_sent)
        self.assertTrue(notification.email_sent)
        self.assertIsNotNone(notification.sms_sent_at)
        self.assertIsNotNone(notification.email_sent_at)

        # Verify webhook was called with correct payload
        self.assertEqual(mock_post.call_count, 1)
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        self.assertEqual(payload['event'], 'booking_confirmed')
        self.assertEqual(payload['notification_id'], str(notification.id))
        self.assertEqual(payload['channels']['sms'], True)
        self.assertEqual(payload['channels']['email'], True)
        self.assertEqual(payload['recipients']['phone'], self.customer.phone)
        self.assertEqual(payload['recipients']['email'], self.customer.email)

    @override_settings(N8N_WEBHOOK_URL='')
    def test_trigger_n8n_webhook_no_url_fails(self):
        """n8n webhook fails if URL not configured."""
        notification = Notification.objects.create(
            user=self.customer,
            type='booking_confirmed',
            title='Test',
            message='Test',
        )

        with self.assertRaises(ValidationError) as ctx:
            NotificationService.trigger_n8n_webhook(
                notification=notification,
                send_sms=True
            )
        
        self.assertIn('NOT-SERV-CONF-001', str(ctx.exception))

    @patch('apps.common.notification_service.requests.post')
    @patch('time.sleep')  # Mock sleep to speed up test
    @override_settings(N8N_WEBHOOK_URL='https://n8n.example.com/webhook')
    def test_trigger_n8n_webhook_retries_on_failure(self, mock_sleep, mock_post):
        """n8n webhook retries on failure with exponential backoff."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        notification = Notification.objects.create(
            user=self.customer,
            type='booking_confirmed',
            title='Test',
            message='Test',
        )

        success = NotificationService.trigger_n8n_webhook(
            notification=notification,
            send_sms=True
        )

        self.assertFalse(success)
        # Should retry 3 times
        self.assertEqual(mock_post.call_count, 3)
        # Sleep called 2 times (not after last attempt)
        self.assertEqual(mock_sleep.call_count, 2)

    def test_mark_as_read(self):
        """Marking notification as read updates is_read flag."""
        notification = Notification.objects.create(
            user=self.customer,
            type='booking_confirmed',
            title='Test',
            message='Test',
            is_read=False,
        )

        NotificationService.mark_as_read(notification=notification)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_get_unread_count(self):
        """get_unread_count returns correct count."""
        # Create 3 unread notifications
        for i in range(3):
            Notification.objects.create(
                user=self.customer,
                type='booking_confirmed',
                title=f'Test {i}',
                message='Test',
                is_read=False,
            )
        
        # Create 2 read notifications
        for i in range(2):
            Notification.objects.create(
                user=self.customer,
                type='booking_confirmed',
                title=f'Read {i}',
                message='Test',
                is_read=True,
            )

        count = NotificationService.get_unread_count(user=self.customer)
        self.assertEqual(count, 3)


class NotificationTaskTest(TestCase):
    """Test Celery tasks for notifications."""

    def setUp(self):
        """Create test data."""
        self.customer = CustomUser(
            phone='+919876543210',
            username='+919876543210',
            name='Test Customer',
            role='customer',
            is_active=True,
        )
        self.customer.save(skip_validation=True)

        self.operator = CustomUser(
            phone='+919876543211',
            username='+919876543211',
            name='Test Operator',
            role='operator',
            is_verified=True,
            is_active=True,
        )
        self.operator.save(skip_validation=True)

        self.bus = Bus(
            operator=self.operator,
            name='Test Bus',
            registration_number='RJ01AB1234',
            bus_type='medium_bus',
            seating_capacity=40,
            ac_type='ac',
            price_per_km=Decimal('20.00'),
            base_price=Decimal('2500.00'),
            base_city='Jaipur',
            is_active=True,
            approval_status='approved',
        )
        self.bus.save()

    @patch('apps.common.tasks.NotificationService.trigger_n8n_webhook')
    def test_send_notification_via_n8n_task(self, mock_trigger):
        """Celery task sends notification via n8n."""
        mock_trigger.return_value = True

        notification = Notification.objects.create(
            user=self.customer,
            type='booking_confirmed',
            title='Test',
            message='Test',
        )

        result = send_notification_via_n8n(
            notification_id=str(notification.id),
            send_sms=True,
            send_email=True
        )

        self.assertTrue(result)
        mock_trigger.assert_called_once_with(
            notification=notification,
            send_sms=True,
            send_email=True
        )

    def test_send_trip_reminders_task(self):
        """send_trip_reminders sends reminders for bookings 6h before pickup."""
        # Create booking with pickup in 6 hours
        now = timezone.now()
        pickup_datetime = now + timedelta(hours=6)
        
        booking = Booking(
            customer=self.customer,
            operator=self.operator,
            bus=self.bus,
            trip_type='one_way',
            pickup_location='Jaipur',
            drop_location='Delhi',
            pickup_date=pickup_datetime.date(),
            pickup_time=pickup_datetime.time(),
            passenger_count=30,
            base_amount=Decimal('5000'),
            total_amount=Decimal('5500'),
            status='confirmed',
        )
        booking.save()

        # Run task
        with patch('apps.common.tasks.NotificationService.create_notification') as mock_notify:
            stats = send_trip_reminders()

            # Should have sent 1 reminder
            self.assertEqual(stats['sent_count'], 1)
            mock_notify.assert_called_once()
            
            # Verify notification parameters
            call_args = mock_notify.call_args
            self.assertEqual(call_args[1]['user'], self.customer)
            self.assertEqual(call_args[1]['notification_type'], 'trip_reminder')
            self.assertTrue(call_args[1]['send_sms'])
            self.assertFalse(call_args[1]['send_email'])

        # Verify reminder marked as sent
        booking.refresh_from_db()
        self.assertTrue(booking.metadata.get('reminder_sent'))


class NotificationIntegrationTest(TestCase):
    """Test notification integration with booking flow."""

    def setUp(self):
        """Create test data."""
        self.customer = CustomUser(
            phone='+919876543210',
            username='+919876543210',
            name='Test Customer',
            role='customer',
            is_active=True,
        )
        self.customer.save(skip_validation=True)

        self.operator = CustomUser(
            phone='+919876543211',
            username='+919876543211',
            name='Test Operator',
            role='operator',
            is_verified=True,
            is_active=True,
        )
        self.operator.save(skip_validation=True)

        self.bus = Bus(
            operator=self.operator,
            name='Test Bus',
            registration_number='RJ01AB1234',
            bus_type='medium_bus',
            seating_capacity=40,
            ac_type='ac',
            price_per_km=Decimal('20.00'),
            base_price=Decimal('2500.00'),
            base_city='Jaipur',
            is_active=True,
            approval_status='approved',
        )
        self.bus.save()

    @patch('apps.common.tasks.send_notification_via_n8n.delay')
    def test_booking_created_sends_notifications(self, mock_task):
        """Creating booking triggers notifications to customer and operator."""
        from apps.bookings.services import BookingService

        validated_data = {
            'bus': self.bus,
            'trip_type': 'one_way',
            'pickup_location': 'Jaipur',
            'drop_location': 'Delhi',
            'pickup_date': date.today() + timedelta(days=7),
            'pickup_time': datetime.now().time(),
            'passenger_count': 30,
            'estimated_km': Decimal('280'),
        }

        booking = BookingService.create_booking(
            customer=self.customer,
            validated_data=validated_data
        )

        # Should create 2 notifications (customer + operator)
        notifications = Notification.objects.filter(
            type='booking_created'
        )
        self.assertEqual(notifications.count(), 2)

        # Verify customer notification
        customer_notif = notifications.filter(user=self.customer).first()
        self.assertIsNotNone(customer_notif)
        self.assertIn(booking.booking_number, customer_notif.title)
        self.assertIn(booking.bus.name, customer_notif.message)

        # Verify operator notification
        operator_notif = notifications.filter(user=self.operator).first()
        self.assertIsNotNone(operator_notif)
        self.assertIn(booking.booking_number, operator_notif.title)
        self.assertIn(self.customer.name, operator_notif.message)

    @patch('apps.common.tasks.send_notification_via_n8n.delay')
    def test_booking_confirmed_sends_notification(self, mock_task):
        """Confirming booking sends notification to customer."""
        from apps.bookings.services import BookingService

        booking = Booking(
            customer=self.customer,
            operator=self.operator,
            bus=self.bus,
            trip_type='one_way',
            pickup_location='Jaipur',
            drop_location='Delhi',
            pickup_date=date.today() + timedelta(days=7),
            pickup_time=datetime.now().time(),
            passenger_count=30,
            base_amount=Decimal('5000'),
            total_amount=Decimal('5500'),
            status='pending',
        )
        booking.save()

        # Confirm booking
        BookingService.respond_to_booking(
            booking=booking,
            new_status='confirmed',
            responded_by=self.operator
        )

        # Should create confirmation notification
        notification = Notification.objects.filter(
            type='booking_confirmed',
            user=self.customer
        ).first()

        self.assertIsNotNone(notification)
        self.assertIn('confirmed', notification.title.lower())
        self.assertIn(booking.booking_number, notification.message)

    @patch('apps.common.tasks.send_notification_via_n8n.delay')
    def test_booking_rejected_sends_notification(self, mock_task):
        """Rejecting booking sends notification to customer."""
        from apps.bookings.services import BookingService

        booking = Booking(
            customer=self.customer,
            operator=self.operator,
            bus=self.bus,
            trip_type='one_way',
            pickup_location='Jaipur',
            drop_location='Delhi',
            pickup_date=date.today() + timedelta(days=7),
            pickup_time=datetime.now().time(),
            passenger_count=30,
            base_amount=Decimal('5000'),
            total_amount=Decimal('5500'),
            status='pending',
        )
        booking.save()

        # Reject booking
        BookingService.respond_to_booking(
            booking=booking,
            new_status='rejected',
            reason='Bus under maintenance',
            responded_by=self.operator
        )

        # Should create rejection notification
        notification = Notification.objects.filter(
            type='booking_rejected',
            user=self.customer
        ).first()

        self.assertIsNotNone(notification)
        self.assertIn('rejected', notification.title.lower())
        self.assertIn('Bus under maintenance', notification.message)
