"""Tests for buses app – models, services, views, serializers.

Covers: Bus, BusPhoto, BusAmenity, AvailabilityBlock, BusService,
and all bus ViewSets.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from apps.buses.models import AvailabilityBlock, Bus, BusAmenity, BusPhoto
from apps.buses.serializers import BusCreateUpdateSerializer
from apps.buses.services import BusService
from apps.users.models import CustomUser


# ═══════════════════════════════════════════════════════════════
#  MODEL TESTS
# ═══════════════════════════════════════════════════════════════


class BusModelTest(TestCase):
    """Test Bus model creation, validation, and business methods."""

    def setUp(self) -> None:
        """Create an operator and bus."""
        self.operator = CustomUser(
            phone='+919100000001',
            username='+919100000001',
            name='Bus Operator',
            role='operator',
            business_name='Test Travels',
            commission_rate=Decimal('10.00'),
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)

        self.bus = Bus(
            operator=self.operator,
            name='Test Bus',
            bus_type='mini_bus',
            seating_capacity=17,
            registration_number='RJ14AB0001',
            ac_type='ac',
            price_per_km=Decimal('25.00'),
            base_price=Decimal('2000.00'),
            base_city='Jaipur',
        )
        self.bus.save()

    def test_create_bus(self) -> None:
        """Verify bus creation with required fields."""
        self.assertEqual(self.bus.name, 'Test Bus')
        self.assertEqual(self.bus.operator, self.operator)
        self.assertFalse(self.bus.is_approved)
        self.assertEqual(self.bus.approval_status, 'pending')

    def test_str_representation(self) -> None:
        """Bus __str__ includes name and registration."""
        self.assertIn('Test Bus', str(self.bus))
        self.assertIn('RJ14AB0001', str(self.bus))

    def test_is_available_on_unblocked_date(self) -> None:
        """Bus should be available on unblocked dates."""
        self.assertTrue(self.bus.is_available_on(dt.date(2026, 12, 25)))

    def test_is_not_available_on_blocked_date(self) -> None:
        """Bus should not be available on blocked dates."""
        AvailabilityBlock.objects.create(
            bus=self.bus,
            blocked_date=dt.date(2026, 12, 25),
            block_reason='maintenance',
        )
        self.assertFalse(self.bus.is_available_on(dt.date(2026, 12, 25)))

    def test_calculate_trip_cost(self) -> None:
        """Trip cost calculation should return correct breakdown."""
        cost = self.bus.calculate_trip_cost(100)
        self.assertEqual(cost['base_price'], Decimal('2000.00'))
        self.assertEqual(cost['distance_charge'], Decimal('2500.00'))
        self.assertEqual(cost['estimated_total'], Decimal('4500.00'))

    def test_bus_models_val_001_empty_name(self) -> None:
        """BUS-MODELS-VAL-001: Bus name required."""
        self.bus.name = ''
        with self.assertRaises(DjangoValidationError):
            self.bus.full_clean()

    def test_bus_models_val_002_excessive_capacity(self) -> None:
        """BUS-MODELS-VAL-002: Capacity cannot exceed 60."""
        self.bus.seating_capacity = 80
        with self.assertRaises(DjangoValidationError):
            self.bus.full_clean()

    def test_bus_models_val_003_negative_base_price(self) -> None:
        """BUS-MODELS-VAL-003: Base price must be non-negative."""
        self.bus.base_price = Decimal('-100')
        with self.assertRaises(DjangoValidationError):
            self.bus.full_clean()


class BusPhotoModelTest(TestCase):
    """Test BusPhoto model."""

    def setUp(self) -> None:
        """Create bus for photo tests."""
        self.operator = CustomUser(
            phone='+919100000002', username='+919100000002',
            role='operator',
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)

        self.bus = Bus(
            operator=self.operator, name='Photo Bus', bus_type='mini_bus',
            seating_capacity=17, registration_number='RJ14CD0002',
            ac_type='ac', price_per_km=Decimal('20.00'), base_city='Jaipur',
        )
        self.bus.save()

    def test_create_photo(self) -> None:
        """Verify photo creation."""
        photo = BusPhoto.objects.create(
            bus=self.bus,
            photo_url='https://example.com/bus.jpg',
            photo_type='exterior_front',
            is_primary=True,
        )
        self.assertTrue(photo.is_primary)


class AvailabilityBlockModelTest(TestCase):
    """Test AvailabilityBlock model."""

    def setUp(self) -> None:
        """Create bus for block tests."""
        self.operator = CustomUser(
            phone='+919100000003', username='+919100000003',
            role='operator',
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)

        self.bus = Bus(
            operator=self.operator, name='Block Bus', bus_type='mini_bus',
            seating_capacity=17, registration_number='RJ14EF0003',
            ac_type='ac', price_per_km=Decimal('20.00'), base_city='Jaipur',
        )
        self.bus.save()

    def test_create_block(self) -> None:
        """Verify availability block creation."""
        block = AvailabilityBlock.objects.create(
            bus=self.bus,
            blocked_date=dt.date(2026, 12, 31),
            block_reason='maintenance',
        )
        self.assertEqual(block.block_reason, 'maintenance')

    def test_unique_block_per_date(self) -> None:
        """Cannot create duplicate blocks on same date."""
        AvailabilityBlock.objects.create(
            bus=self.bus,
            blocked_date=dt.date(2026, 12, 31),
            block_reason='maintenance',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AvailabilityBlock.objects.create(
                bus=self.bus,
                blocked_date=dt.date(2026, 12, 31),
                block_reason='personal',
            )


# ═══════════════════════════════════════════════════════════════
#  SERVICE TESTS
# ═══════════════════════════════════════════════════════════════


class BusServiceTest(TestCase):
    """Test BusService – search and approval."""

    def setUp(self) -> None:
        """Create buses for search tests."""
        self.operator = CustomUser(
            phone='+919100000010', username='+919100000010',
            role='operator', business_name='Search Travels',
            commission_rate=Decimal('10.00'),
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)

        self.bus = Bus(
            operator=self.operator, name='Search Bus', bus_type='mini_bus',
            seating_capacity=17, registration_number='RJ14GH0010',
            ac_type='ac', price_per_km=Decimal('20.00'), base_city='Jaipur',
            is_active=True, approval_status='approved',
        )
        self.bus.save()

    def test_search_available_no_filters(self) -> None:
        """Search with no filters returns all approved buses."""
        result = BusService.search_available()
        self.assertEqual(result.count(), 1)

    def test_search_by_city(self) -> None:
        """Search with city filter."""
        result = BusService.search_available(city='Jaipur')
        self.assertEqual(result.count(), 1)

        result = BusService.search_available(city='Delhi')
        self.assertEqual(result.count(), 0)

    def test_search_by_passengers(self) -> None:
        """Search by minimum passenger capacity."""
        result = BusService.search_available(passengers=17)
        self.assertEqual(result.count(), 1)

        result = BusService.search_available(passengers=50)
        self.assertEqual(result.count(), 0)

    def test_search_by_date_available(self) -> None:
        """Search on unblocked date finds bus."""
        result = BusService.search_available(date='2026-12-25')
        self.assertEqual(result.count(), 1)

    def test_search_by_date_blocked(self) -> None:
        """Search on blocked date excludes bus."""
        AvailabilityBlock.objects.create(
            bus=self.bus,
            blocked_date=dt.date(2026, 12, 25),
            block_reason='booked_platform',
        )
        result = BusService.search_available(date='2026-12-25')
        self.assertEqual(result.count(), 0)

    def test_search_invalid_date_com_utils_val_001(self) -> None:
        """COM-UTILS-VAL-001: Invalid date format."""
        with self.assertRaises(ValidationError) as ctx:
            BusService.search_available(date='25-12-2026')
        self.assertEqual(ctx.exception.detail[0].code, 'COM-UTILS-VAL-001')

    def test_approve_bus(self) -> None:
        """Admin approves a bus."""
        self.bus.approval_status = 'pending'
        self.bus.save()
        bus = BusService.approve_bus(bus=self.bus, action='approve')
        self.assertEqual(bus.approval_status, 'approved')

    def test_reject_bus(self) -> None:
        """Admin rejects a bus."""
        bus = BusService.approve_bus(bus=self.bus, action='reject')
        self.assertEqual(bus.approval_status, 'rejected')

    def test_invalid_approve_action_bus_serv_val_001(self) -> None:
        """BUS-SERV-VAL-001: Invalid approval action."""
        with self.assertRaises(ValidationError) as ctx:
            BusService.approve_bus(bus=self.bus, action='maybe')
        self.assertEqual(ctx.exception.detail[0].code, 'BUS-SERV-VAL-001')

    def test_block_date_bus_serv_conflict_001(self) -> None:
        """BUS-SERV-CONFLICT-001: Bus already blocked on this date."""
        BusService.block_date(
            bus=self.bus,
            blocked_date=dt.date(2026, 12, 25),
        )
        with self.assertRaises(ValidationError) as ctx:
            BusService.block_date(
                bus=self.bus,
                blocked_date=dt.date(2026, 12, 25),
            )
        self.assertEqual(ctx.exception.detail[0].code, 'BUS-SERV-CONFLICT-001')


# ═══════════════════════════════════════════════════════════════
#  SERIALIZER TESTS
# ═══════════════════════════════════════════════════════════════


class BusCreateUpdateSerializerTest(TestCase):
    """Test BusCreateUpdateSerializer validation."""

    def test_valid_bus_data(self) -> None:
        """Valid bus data passes validation."""
        data = {
            'name': 'Test Bus',
            'bus_type': 'mini_bus',
            'seating_capacity': 17,
            'registration_number': 'RJ14XY9999',
            'ac_type': 'ac',
            'price_per_km': '25.00',
            'base_city': 'Jaipur',
        }
        ser = BusCreateUpdateSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_bus_serial_val_001_low_capacity(self) -> None:
        """BUS-SERIAL-VAL-001: Capacity too low."""
        data = {
            'name': 'Test', 'bus_type': 'mini_bus',
            'seating_capacity': 0, 'registration_number': 'RJ14XY9998',
            'ac_type': 'ac', 'price_per_km': '25.00', 'base_city': 'Jaipur',
        }
        ser = BusCreateUpdateSerializer(data=data)
        self.assertFalse(ser.is_valid())

    def test_bus_serial_val_002_high_capacity(self) -> None:
        """BUS-SERIAL-VAL-002: Capacity too high."""
        data = {
            'name': 'Test', 'bus_type': 'mini_bus',
            'seating_capacity': 150, 'registration_number': 'RJ14XY9997',
            'ac_type': 'ac', 'price_per_km': '25.00', 'base_city': 'Jaipur',
        }
        ser = BusCreateUpdateSerializer(data=data)
        self.assertFalse(ser.is_valid())

    def test_bus_serial_val_003_negative_price(self) -> None:
        """BUS-SERIAL-VAL-003: Price per km must be positive."""
        data = {
            'name': 'Test', 'bus_type': 'mini_bus',
            'seating_capacity': 17, 'registration_number': 'RJ14XY9996',
            'ac_type': 'ac', 'price_per_km': '-5.00', 'base_city': 'Jaipur',
        }
        ser = BusCreateUpdateSerializer(data=data)
        self.assertFalse(ser.is_valid())


# ═══════════════════════════════════════════════════════════════
#  API / VIEW TESTS
# ═══════════════════════════════════════════════════════════════


class BusViewSetAPITest(APITestCase):
    """Test bus API endpoints."""

    def setUp(self) -> None:
        """Create users, buses, and tokens."""
        from rest_framework.authtoken.models import Token

        self.operator = CustomUser(
            phone='+919100000020', username='+919100000020',
            name='Operator', role='operator', business_name='View Travels',
            commission_rate=Decimal('10.00'),
        )
        self.operator.set_password('test123')
        self.operator.save(skip_validation=True)
        self.op_token = Token.objects.create(user=self.operator)

        self.admin = CustomUser(
            phone='+919100000021', username='+919100000021',
            name='Admin', role='admin', is_staff=True,
        )
        self.admin.set_password('test123')
        self.admin.save(skip_validation=True)
        self.admin_token = Token.objects.create(user=self.admin)

        self.customer = CustomUser(
            phone='+919100000022', username='+919100000022',
            name='Customer', role='customer',
        )
        self.customer.set_password('test123')
        self.customer.save(skip_validation=True)
        self.cust_token = Token.objects.create(user=self.customer)

        self.other_operator = CustomUser(
            phone='+919100000023', username='+919100000023',
            name='Other Operator', role='operator', business_name='Other Travels',
            commission_rate=Decimal('10.00'),
        )
        self.other_operator.set_password('test123')
        self.other_operator.save(skip_validation=True)
        self.other_op_token = Token.objects.create(user=self.other_operator)

        self.bus = Bus(
            operator=self.operator, name='API Bus', bus_type='mini_bus',
            seating_capacity=17, registration_number='RJ14MN0020',
            ac_type='ac', price_per_km=Decimal('20.00'), base_city='Jaipur',
            is_active=True, approval_status='approved',
        )
        self.bus.save()

        self.bus_photo = BusPhoto.objects.create(
            bus=self.bus,
            photo_url='https://example.com/api-bus.jpg',
            photo_type='exterior_front',
            is_primary=True,
        )
        self.bus_amenity = BusAmenity.objects.create(
            bus=self.bus,
            amenity='wifi',
        )
        self.availability_block = AvailabilityBlock.objects.create(
            bus=self.bus,
            blocked_date=dt.date(2026, 12, 31),
            block_reason='maintenance',
        )

        self.client = APIClient()

    def test_list_buses_public(self) -> None:
        """GET /buses/ returns approved buses without auth."""
        resp = self.client.get('/api/v1/buses/')
        self.assertEqual(resp.status_code, 200)

    def test_operator_create_bus(self) -> None:
        """POST /buses/ by operator creates bus."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.op_token.key}')
        data = {
            'name': 'New Bus', 'bus_type': 'mini_bus',
            'seating_capacity': 17, 'registration_number': 'RJ14PQ0099',
            'ac_type': 'ac', 'price_per_km': '20.00', 'base_city': 'Delhi',
        }
        resp = self.client.post('/api/v1/buses/', data, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_customer_cannot_create_bus_perm_001(self) -> None:
        """BUS-VIEWS-PERM-001: Only operators can create buses."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.cust_token.key}')
        data = {
            'name': 'Bad Bus', 'bus_type': 'mini_bus',
            'seating_capacity': 17, 'registration_number': 'RJ14ZZ9999',
            'ac_type': 'ac', 'price_per_km': '20.00', 'base_city': 'Delhi',
        }
        resp = self.client.post('/api/v1/buses/', data, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_operator_my_buses(self) -> None:
        """GET /buses/my_buses/ returns operator's buses."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.op_token.key}')
        resp = self.client.get('/api/v1/buses/my_buses/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_admin_approve_bus(self) -> None:
        """POST /buses/{id}/approve/ by admin approves bus."""
        self.bus.approval_status = 'pending'
        self.bus.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        resp = self.client.post(
            f'/api/v1/buses/{self.bus.id}/approve/',
            {'action': 'approve'}, format='json',
        )
        self.assertEqual(resp.status_code, 200)

    def test_search_buses(self) -> None:
        """POST /buses/search/ returns matching buses."""
        resp = self.client.post(
            '/api/v1/buses/search/',
            {'city': 'Jaipur'}, format='json',
        )
        self.assertEqual(resp.status_code, 200)

    def test_other_operator_cannot_access_foreign_bus_photos(self) -> None:
        """Nested photos endpoint should hide foreign operator resources."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_op_token.key}')

        list_resp = self.client.get(f'/api/v1/buses/{self.bus.id}/photos/')
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data['count'], 0)

        detail_resp = self.client.get(
            f'/api/v1/buses/{self.bus.id}/photos/{self.bus_photo.id}/',
        )
        self.assertEqual(detail_resp.status_code, 404)

    def test_other_operator_cannot_access_foreign_bus_amenities(self) -> None:
        """Nested amenities endpoint should hide foreign operator resources."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_op_token.key}')

        list_resp = self.client.get(f'/api/v1/buses/{self.bus.id}/amenities/')
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data['count'], 0)

        detail_resp = self.client.delete(
            f'/api/v1/buses/{self.bus.id}/amenities/{self.bus_amenity.id}/',
        )
        self.assertEqual(detail_resp.status_code, 404)

    def test_other_operator_cannot_access_foreign_bus_availability_blocks(self) -> None:
        """Nested availability endpoint should hide foreign operator resources."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_op_token.key}')

        list_resp = self.client.get(f'/api/v1/buses/{self.bus.id}/availability/')
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data['count'], 0)

        detail_resp = self.client.delete(
            f'/api/v1/buses/{self.bus.id}/availability/{self.availability_block.id}/',
        )
        self.assertEqual(detail_resp.status_code, 404)
