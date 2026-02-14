"""Tests for users app – models, services, views, serializers.

Covers: CustomUser, Document, Notification, AuthService, UserService,
DocumentService, OperatorService, and all user ViewSets.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from apps.users.models import CustomUser, Document, Notification
from apps.users.serializers import RegisterSerializer
from apps.users.services import (
    AuthService,
    DocumentService,
    OperatorService,
    UserService,
    get_supabase_client,
)


# ═══════════════════════════════════════════════════════════════
#  MODEL TESTS
# ═══════════════════════════════════════════════════════════════


class CustomUserModelTest(TestCase):
    """Test CustomUser model creation, validation, and business methods."""

    def setUp(self) -> None:
        """Create a base user for tests."""
        self.user = CustomUser(
            phone='+919667907515',
            username='+919667907515',
            name='Test User',
            role='customer',
        )
        self.user.set_password('test123')
        self.user.save(skip_validation=True)

    def test_create_customer(self) -> None:
        """Verify customer creation with phone-based auth."""
        self.assertEqual(self.user.phone, '+919667907515')
        self.assertEqual(self.user.role, 'customer')
        self.assertTrue(self.user.is_customer)
        self.assertFalse(self.user.is_operator)
        self.assertFalse(self.user.is_admin_user)

    def test_str_representation(self) -> None:
        """User __str__ includes name and phone."""
        self.assertIn('Test User', str(self.user))
        self.assertIn('+919667907515', str(self.user))

    def test_operator_creation(self) -> None:
        """Verify operator-specific fields."""
        operator = CustomUser(
            phone='+919000000001',
            username='+919000000001',
            name='Test Operator',
            role='operator',
            business_name='Test Travel Co',
            business_type='company',
        )
        operator.set_password('test123')
        operator.save(skip_validation=True)
        self.assertTrue(operator.is_operator)
        self.assertEqual(operator.business_name, 'Test Travel Co')

    def test_has_active_subscription_free(self) -> None:
        """Free tier should have no active subscription."""
        self.assertFalse(self.user.has_active_subscription())

    def test_uuid_primary_key(self) -> None:
        """Verify UUID is auto-generated."""
        self.assertIsNotNone(self.user.id)
        self.assertEqual(len(str(self.user.id)), 36)


class DocumentModelTest(TestCase):
    """Test Document model validation and business methods."""

    def setUp(self) -> None:
        """Create a user and document for tests."""
        self.user = CustomUser(
            phone='+919000000002',
            username='+919000000002',
            name='Doc User',
            role='operator',
        )
        self.user.set_password('test123')
        self.user.save(skip_validation=True)

    def test_create_document(self) -> None:
        """Verify document creation with required fields."""
        doc = Document.objects.create(
            user=self.user,
            document_type='aadhar',
            document_url='https://example.com/aadhar.pdf',
            document_number='1234-5678-9012',
        )
        self.assertEqual(doc.verification_status, 'pending')
        self.assertFalse(doc.is_expired)

    def test_expired_document(self) -> None:
        """Document with past expiry should be marked expired."""
        doc = Document(
            user=self.user,
            document_type='insurance',
            document_url='https://example.com/insurance.pdf',
            expiry_date=date.today() - timedelta(days=1),
        )
        # Skip save validation to test is_expired property
        doc.save_base = lambda *a, **k: None
        self.assertTrue(doc.is_expired)

    def test_doc_models_val_002_future_expiry(self) -> None:
        """DOC-MODELS-VAL-002: Expiry date must be in the future."""
        doc = Document(
            user=self.user,
            document_type='insurance',
            document_url='https://example.com/insurance.pdf',
            expiry_date=date.today() - timedelta(days=1),
        )
        with self.assertRaises(DjangoValidationError) as ctx:
            doc.clean()
        self.assertEqual(ctx.exception.code, 'DOC-MODELS-VAL-002')


class NotificationModelTest(TestCase):
    """Test Notification model."""

    def setUp(self) -> None:
        """Create a user for notification tests."""
        self.user = CustomUser(
            phone='+919000000003',
            username='+919000000003',
            name='Notif User',
        )
        self.user.set_password('test123')
        self.user.save(skip_validation=True)

    def test_create_notification(self) -> None:
        """Verify notification creation."""
        notif = Notification.objects.create(
            user=self.user,
            type='booking_confirmed',
            title='Booking Confirmed',
            message='Your booking #123 is confirmed.',
        )
        self.assertFalse(notif.is_read)
        self.assertIn('Booking Confirmed', str(notif))


# ═══════════════════════════════════════════════════════════════
#  SERVICE TESTS
# ═══════════════════════════════════════════════════════════════


class AuthServiceTest(TestCase):
    """Test AuthService – OTP send/verify via Supabase."""

    def setUp(self) -> None:
        get_supabase_client.cache_clear()

    def tearDown(self) -> None:
        get_supabase_client.cache_clear()

    @patch('supabase.create_client')
    def test_send_otp_success(self, mock_client) -> None:
        """send_otp should return success message."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase

        result = AuthService.send_otp(phone='+919000000010')
        self.assertEqual(result['message'], 'OTP sent successfully')

    @patch('supabase.create_client')
    def test_send_otp_failure_usr_serv_api_001(self, mock_client) -> None:
        """USR-SERV-API-001: Failed to send OTP."""
        mock_client.side_effect = Exception('Network error')

        with self.assertRaises(ValidationError) as ctx:
            AuthService.send_otp(phone='+919000000010')
        self.assertEqual(ctx.exception.detail[0].code, 'USR-SERV-API-001')

    @patch('supabase.create_client')
    def test_verify_otp_invalid_usr_serv_auth_001(self, mock_client) -> None:
        """USR-SERV-AUTH-001: Invalid OTP."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        mock_resp = MagicMock()
        mock_resp.user = None
        mock_supabase.auth.verify_otp.return_value = mock_resp

        with self.assertRaises(ValidationError) as ctx:
            AuthService.verify_otp(phone='+919000000010', otp='000000')
        self.assertEqual(ctx.exception.detail[0].code, 'USR-SERV-AUTH-001')


class OperatorServiceTest(TestCase):
    """Test OperatorService."""

    def setUp(self) -> None:
        """Create a customer user."""
        self.user = CustomUser(
            phone='+919000000020',
            username='+919000000020',
            name='Customer User',
            role='customer',
        )
        self.user.set_password('test123')
        self.user.save(skip_validation=True)

    def test_register_as_operator(self) -> None:
        """Convert customer to operator."""
        user = OperatorService.register_as_operator(
            user=self.user,
            validated_data={
                'business_name': 'Lucky Travels',
                'city': 'Jaipur',
            },
        )
        self.assertEqual(user.role, 'operator')
        self.assertEqual(user.business_name, 'Lucky Travels')

    def test_already_operator_usr_serv_conflict_001(self) -> None:
        """USR-SERV-CONFLICT-001: Already an operator."""
        self.user.role = 'operator'
        self.user.save(skip_validation=True)

        with self.assertRaises(ValidationError) as ctx:
            OperatorService.register_as_operator(
                user=self.user,
                validated_data={'business_name': 'Test'},
            )
        self.assertEqual(ctx.exception.detail[0].code, 'USR-SERV-CONFLICT-001')


class UserServiceTest(TestCase):
    """Test UserService verify_user."""

    def setUp(self) -> None:
        """Create an operator user."""
        self.operator = CustomUser(
            phone='+919000000030',
            username='+919000000030',
            name='Pending Operator',
            role='operator',
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)

    def test_verify_user_approve(self) -> None:
        """Admin approves an operator."""
        user = UserService.verify_user(
            user=self.operator,
            action='approve',
        )
        self.assertTrue(user.is_verified)
        self.assertEqual(user.verification_status, 'verified')
        self.assertIsNotNone(user.verified_at)

    def test_verify_user_reject(self) -> None:
        """Admin rejects an operator."""
        user = UserService.verify_user(
            user=self.operator,
            action='reject',
            reason='Incomplete documents',
        )
        self.assertFalse(user.is_verified)
        self.assertEqual(user.verification_status, 'rejected')
        self.assertIsNone(user.verified_at)

    def test_verify_user_invalid_action(self) -> None:
        """USR-SERV-VAL-001: Invalid action."""
        with self.assertRaises(ValidationError) as ctx:
            UserService.verify_user(
                user=self.operator,
                action='invalid',
            )
        self.assertEqual(ctx.exception.detail[0].code, 'USR-SERV-VAL-001')


class DocumentServiceTest(TestCase):
    """Test DocumentService verify_document."""

    def setUp(self) -> None:
        """Create operator and document."""
        self.admin = CustomUser(
            phone='+919000000040',
            username='+919000000040',
            name='Admin User',
            role='admin',
            is_staff=True,
        )
        self.admin.set_password('test123')
        self.admin.save(skip_validation=True)

        self.operator = CustomUser(
            phone='+919000000041',
            username='+919000000041',
            name='Op User',
            role='operator',
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)

        self.doc = Document.objects.create(
            user=self.operator,
            document_type='aadhar',
            document_url='https://example.com/aadhar.pdf',
        )

    def test_approve_document(self) -> None:
        """Admin approves a document."""
        doc = DocumentService.verify_document(
            document=self.doc,
            action='approve',
            verified_by=self.admin,
        )
        self.assertEqual(doc.verification_status, 'verified')
        self.assertEqual(doc.verified_by, self.admin)

    def test_reject_document(self) -> None:
        """Admin rejects a document."""
        doc = DocumentService.verify_document(
            document=self.doc,
            action='reject',
            verified_by=self.admin,
            rejection_reason='Blurry image',
        )
        self.assertEqual(doc.verification_status, 'rejected')

    def test_invalid_action_doc_serv_val_001(self) -> None:
        """DOC-SERV-VAL-001: Invalid action."""
        with self.assertRaises(ValidationError) as ctx:
            DocumentService.verify_document(
                document=self.doc,
                action='maybe',
                verified_by=self.admin,
            )
        self.assertEqual(ctx.exception.detail[0].code, 'DOC-SERV-VAL-001')


# ═══════════════════════════════════════════════════════════════
#  SERIALIZER TESTS
# ═══════════════════════════════════════════════════════════════


class RegisterSerializerTest(TestCase):
    """Test RegisterSerializer validation with error codes."""

    def test_valid_registration(self) -> None:
        """Valid data should pass."""
        data = {'phone': '+919667907500', 'name': 'Test', 'role': 'customer'}
        ser = RegisterSerializer(data=data)
        self.assertTrue(ser.is_valid())

    def test_phone_non_digits_usr_serial_val_001(self) -> None:
        """USR-SERIAL-VAL-001: Phone with non-digits."""
        data = {'phone': 'abc123', 'name': 'Test', 'role': 'customer'}
        ser = RegisterSerializer(data=data)
        self.assertFalse(ser.is_valid())

    def test_phone_too_short_usr_serial_val_002(self) -> None:
        """USR-SERIAL-VAL-002: Phone too short."""
        data = {'phone': '12345', 'name': 'Test', 'role': 'customer'}
        ser = RegisterSerializer(data=data)
        self.assertFalse(ser.is_valid())

    def test_invalid_role_usr_serial_val_003(self) -> None:
        """USR-SERIAL-VAL-003: admin not allowed at registration."""
        data = {'phone': '+919667907500', 'name': 'Test', 'role': 'admin'}
        ser = RegisterSerializer(data=data)
        self.assertFalse(ser.is_valid())


# ═══════════════════════════════════════════════════════════════
#  API / VIEW TESTS
# ═══════════════════════════════════════════════════════════════


class UserViewSetAPITest(APITestCase):
    """Test user API endpoints."""

    def setUp(self) -> None:
        """Create users and tokens."""
        from rest_framework.authtoken.models import Token

        self.admin = CustomUser(
            phone='+919000000050',
            username='+919000000050',
            name='Admin',
            role='admin',
            is_staff=True,
            is_superuser=True,
        )
        self.admin.set_password('test123')
        self.admin.save(skip_validation=True)
        self.admin_token = Token.objects.create(user=self.admin)

        self.customer = CustomUser(
            phone='+919000000051',
            username='+919000000051',
            name='Customer',
            role='customer',
        )
        self.customer.set_password('test123')
        self.customer.save(skip_validation=True)
        self.customer_token = Token.objects.create(user=self.customer)

        self.client = APIClient()

    def test_me_endpoint(self) -> None:
        """GET /users/me/ returns authenticated user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        resp = self.client.get('/api/v1/users/users/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['phone'], '+919000000051')

    def test_me_unauthenticated(self) -> None:
        """GET /users/me/ without auth returns 401."""
        resp = self.client.get('/api/v1/users/users/me/')
        self.assertIn(resp.status_code, (401, 403))

    def test_admin_list_users(self) -> None:
        """Admin can list all users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        resp = self.client.get('/api/v1/users/users/')
        self.assertEqual(resp.status_code, 200)

    def test_customer_cannot_list_users(self) -> None:
        """Customer cannot list all users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')
        resp = self.client.get('/api/v1/users/users/')
        self.assertIn(resp.status_code, (403,))


class NotificationViewSetAPITest(APITestCase):
    """Test notification API endpoints."""

    def setUp(self) -> None:
        """Create user with notifications."""
        from rest_framework.authtoken.models import Token

        self.user = CustomUser(
            phone='+919000000060',
            username='+919000000060',
            name='Notif User',
            role='customer',
        )
        self.user.set_password('test123')
        self.user.save(skip_validation=True)
        self.token = Token.objects.create(user=self.user)

        Notification.objects.create(
            user=self.user,
            type='booking_confirmed',
            title='Test Notification',
            message='Test message',
        )

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_list_notifications(self) -> None:
        """GET /notifications/ returns user's notifications."""
        resp = self.client.get('/api/v1/users/notifications/')
        self.assertEqual(resp.status_code, 200)

    def test_mark_all_read(self) -> None:
        """POST /notifications/mark_all_read/ marks all read."""
        resp = self.client.post('/api/v1/users/notifications/mark_all_read/')
        self.assertEqual(resp.status_code, 200)
