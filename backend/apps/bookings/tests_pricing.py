"""Tests for distance calculator and pricing modules.

Covers: geocoding, OSRM distance calculation, pricing formula,
calculate-price API endpoint, and edge cases.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.bookings.distance_calculator import (
    calculate_driving_distance,
    geocode_address,
    get_distance_between_locations,
)
from apps.bookings.pricing import (
    calculate_booking_price,
    calculate_trip_days,
)
from apps.buses.models import Bus
from apps.users.models import CustomUser


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════


def _create_test_users():
    """Create customer and operator users for tests."""
    customer = CustomUser(
        phone='+919300000001', username='+919300000001',
        name='Price Customer', role='customer',
    )
    customer.set_password('test123')
    customer.save(skip_validation=True)

    operator = CustomUser(
        phone='+919300000002', username='+919300000002',
        name='Price Operator', role='operator',
        is_verified=True, verification_status='verified',
        business_name='Price Travels', commission_rate=Decimal('10.00'),
    )
    operator.set_password('test123')
    operator.save(skip_validation=True)

    return customer, operator


def _create_test_bus(operator):
    """Create a test bus with pricing fields."""
    bus = Bus(
        operator=operator, name='Price Test Bus', bus_type='mini_bus',
        seating_capacity=17, registration_number='RJ14PC0001',
        ac_type='ac', price_per_km=Decimal('18.50'),
        base_price=Decimal('3000.00'),
        driver_charge=Decimal('500.00'),
        night_charge=Decimal('1000.00'),
        base_city='Jaipur',
        is_active=True, approval_status='approved',
    )
    bus.save()
    return bus


# ═══════════════════════════════════════════════════════════════
#  PRICING UNIT TESTS (pure calculation, no external APIs)
# ═══════════════════════════════════════════════════════════════


class CalculateTripDaysTest(TestCase):
    """Test trip days calculation from dates."""

    def test_one_way_returns_1(self):
        result = calculate_trip_days(
            pickup_date=dt.date(2026, 3, 15),
            return_date=None,
            trip_type='one_way',
        )
        self.assertEqual(result, 1)

    def test_round_trip_same_day_returns_1(self):
        result = calculate_trip_days(
            pickup_date=dt.date(2026, 3, 15),
            return_date=dt.date(2026, 3, 15),
            trip_type='round_trip',
        )
        self.assertEqual(result, 1)

    def test_round_trip_next_day_returns_2(self):
        result = calculate_trip_days(
            pickup_date=dt.date(2026, 3, 15),
            return_date=dt.date(2026, 3, 16),
            trip_type='round_trip',
        )
        self.assertEqual(result, 2)

    def test_multi_day_3_days(self):
        result = calculate_trip_days(
            pickup_date=dt.date(2026, 3, 15),
            return_date=dt.date(2026, 3, 17),
            trip_type='multi_day',
        )
        self.assertEqual(result, 3)


class PricingCalculatorTest(TestCase):
    """Test charter bus pricing formula."""

    def test_one_way_jaipur_to_bharatpur(self):
        """Jaipur → Bharatpur (156.8 km) one-way pricing."""
        result = calculate_booking_price(
            distance_km=Decimal('156.80'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=1,
            trip_type='one_way',
        )
        # base_fare = max(3000, 18.50 * 156.80) = max(3000, 2900.80) = 3000.00
        self.assertEqual(result['base_fare'], Decimal('3000.00'))
        # driver = 500 * 1 = 500
        self.assertEqual(result['driver_charge'], Decimal('500.00'))
        # night = 1000 * max(0, 1-1) = 0
        self.assertEqual(result['night_charge'], Decimal('0.00'))
        # toll = 3000 * 0.02 = 60
        self.assertEqual(result['toll_estimate'], Decimal('60.00'))
        # subtotal = 3000 + 500 + 0 + 60 = 3560
        self.assertEqual(result['subtotal'], Decimal('3560.00'))
        # platform_fee = max(199, 3560 * 0.03) = max(199, 106.80) = 199
        self.assertEqual(result['platform_fee'], Decimal('199.00'))
        # total = 3560 + 199 = 3759
        self.assertEqual(result['total'], Decimal('3759.00'))

    def test_distance_based_exceeds_base_price(self):
        """When distance charge > base_price, use distance charge."""
        result = calculate_booking_price(
            distance_km=Decimal('300.00'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=1,
            trip_type='one_way',
        )
        # 18.50 * 300 = 5550 > 3000
        self.assertEqual(result['base_fare'], Decimal('5550.00'))

    def test_round_trip_doubles_distance(self):
        """Round trip should double the effective distance."""
        result = calculate_booking_price(
            distance_km=Decimal('156.80'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=2,
            trip_type='round_trip',
        )
        # effective distance = 156.80 * 2 = 313.60
        self.assertEqual(result['effective_distance_km'], Decimal('313.60'))
        # 18.50 * 313.60 = 5801.60 > 3000
        self.assertEqual(result['base_fare'], Decimal('5801.60'))
        # night = 1000 * (2-1) = 1000
        self.assertEqual(result['night_charge'], Decimal('1000.00'))

    def test_multi_day_adds_driver_and_night(self):
        """Multi-day trip: driver charge × days, night halt × (days-1)."""
        result = calculate_booking_price(
            distance_km=Decimal('200.00'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=3,
            trip_type='multi_day',
        )
        # driver = 500 * 3 = 1500
        self.assertEqual(result['driver_charge'], Decimal('1500.00'))
        # night = 1000 * 2 = 2000
        self.assertEqual(result['night_charge'], Decimal('2000.00'))
        self.assertEqual(result['night_count'], 2)

    def test_minimum_base_price_enforced(self):
        """Short distance uses minimum base_price."""
        result = calculate_booking_price(
            distance_km=Decimal('10.00'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=1,
            trip_type='one_way',
        )
        # 18.50 * 10 = 185 < 3000 → use 3000
        self.assertEqual(result['base_fare'], Decimal('3000.00'))

    def test_commission_calculation(self):
        """Commission is calculated correctly on subtotal."""
        result = calculate_booking_price(
            distance_km=Decimal('100.00'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=1,
            trip_type='one_way',
            commission_rate=Decimal('10.00'),
        )
        subtotal = result['subtotal']
        expected_commission = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        self.assertEqual(result['commission_amount'], expected_commission)
        self.assertEqual(
            result['operator_payout'],
            subtotal - expected_commission,
        )

    def test_platform_fee_percentage_when_large(self):
        """Platform fee uses 3% when it exceeds ₹199."""
        result = calculate_booking_price(
            distance_km=Decimal('500.00'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=3,
            trip_type='multi_day',
        )
        # subtotal will be large, 3% should exceed 199
        self.assertGreater(result['platform_fee'], Decimal('199.00'))

    def test_all_values_are_decimal(self):
        """All monetary values should be Decimal."""
        result = calculate_booking_price(
            distance_km=Decimal('100.00'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=1,
            trip_type='one_way',
        )
        for key in ['base_fare', 'driver_charge', 'night_charge',
                     'toll_estimate', 'subtotal', 'platform_fee', 'total',
                     'commission_amount', 'operator_payout']:
            self.assertIsInstance(result[key], Decimal, f'{key} should be Decimal')

    def test_zero_distance(self):
        """Zero distance uses base_price as minimum."""
        result = calculate_booking_price(
            distance_km=Decimal('0'),
            base_price=Decimal('3000.00'),
            price_per_km=Decimal('18.50'),
            driver_charge_per_day=Decimal('500.00'),
            night_halt_charge=Decimal('1000.00'),
            trip_days=1,
            trip_type='one_way',
        )
        self.assertEqual(result['base_fare'], Decimal('3000.00'))


# ═══════════════════════════════════════════════════════════════
#  DISTANCE CALCULATOR TESTS (mocked external APIs)
# ═══════════════════════════════════════════════════════════════


class GeocodeAddressTest(TestCase):
    """Test geocoding with mocked Nominatim API."""

    @patch('apps.bookings.distance_calculator.cache')
    @patch('apps.bookings.distance_calculator.requests.get')
    @patch('apps.bookings.distance_calculator.time.sleep')
    def test_geocode_success(self, mock_sleep, mock_get, mock_cache):
        """Successful geocoding returns lat/lng."""
        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'lat': '26.9124336', 'lon': '75.7872709'},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        lat, lng = geocode_address('Jaipur, Rajasthan')

        self.assertEqual(lat, Decimal('26.9124336'))
        self.assertEqual(lng, Decimal('75.7872709'))
        mock_cache.set.assert_called_once()

    @patch('apps.bookings.distance_calculator.cache')
    def test_geocode_cached(self, mock_cache):
        """Cached results are returned without API call."""
        mock_cache.get.return_value = ('26.9124336', '75.7872709')

        lat, lng = geocode_address('Jaipur, Rajasthan')

        self.assertEqual(lat, Decimal('26.9124336'))
        self.assertEqual(lng, Decimal('75.7872709'))

    def test_geocode_empty_address(self):
        """Empty address raises ValueError."""
        with self.assertRaises(ValueError):
            geocode_address('')

    @patch('apps.bookings.distance_calculator.cache')
    @patch('apps.bookings.distance_calculator.requests.get')
    @patch('apps.bookings.distance_calculator.time.sleep')
    def test_geocode_no_results(self, mock_sleep, mock_get, mock_cache):
        """No results raises ValueError."""
        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            geocode_address('NonExistentPlace12345')
        self.assertIn('Could not find location', str(ctx.exception))

    @patch('apps.bookings.distance_calculator.cache')
    @patch('apps.bookings.distance_calculator.requests.get')
    @patch('apps.bookings.distance_calculator.time.sleep')
    def test_geocode_api_failure(self, mock_sleep, mock_get, mock_cache):
        """API failure raises ValueError."""
        mock_cache.get.return_value = None
        import requests as req
        mock_get.side_effect = req.RequestException('Connection error')

        with self.assertRaises(ValueError) as ctx:
            geocode_address('Jaipur')
        self.assertIn('temporarily unavailable', str(ctx.exception))


class DrivingDistanceTest(TestCase):
    """Test OSRM distance calculation with mocked API."""

    @patch('apps.bookings.distance_calculator.requests.get')
    def test_distance_success(self, mock_get):
        """Successful distance calculation returns km."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': 'Ok',
            'routes': [{'distance': 156800}],  # 156.8 km
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = calculate_driving_distance(
            origin_lat=Decimal('26.9124'),
            origin_lng=Decimal('75.7873'),
            dest_lat=Decimal('27.2152'),
            dest_lng=Decimal('77.4891'),
        )

        self.assertEqual(result, Decimal('156.80'))

    @patch('apps.bookings.distance_calculator.requests.get')
    def test_distance_no_route(self, mock_get):
        """No route raises ValueError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 'NoRoute', 'routes': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            calculate_driving_distance(
                Decimal('26.9124'), Decimal('75.7873'),
                Decimal('0'), Decimal('0'),
            )
        self.assertIn('No driving route', str(ctx.exception))

    @patch('apps.bookings.distance_calculator.requests.get')
    def test_distance_api_failure(self, mock_get):
        """API failure raises ValueError."""
        import requests as req
        mock_get.side_effect = req.RequestException('Timeout')

        with self.assertRaises(ValueError):
            calculate_driving_distance(
                Decimal('26.9124'), Decimal('75.7873'),
                Decimal('27.2152'), Decimal('77.4891'),
            )


class GetDistanceBetweenLocationsTest(TestCase):
    """Test the combined geocode + distance function."""

    @patch('apps.bookings.distance_calculator.calculate_driving_distance')
    @patch('apps.bookings.distance_calculator.geocode_address')
    def test_with_addresses_only(self, mock_geocode, mock_distance):
        """Geocodes both addresses and calculates distance."""
        mock_geocode.side_effect = [
            (Decimal('26.9124'), Decimal('75.7873')),
            (Decimal('27.2152'), Decimal('77.4891')),
        ]
        mock_distance.return_value = Decimal('156.80')

        result = get_distance_between_locations(
            pickup_address='Jaipur',
            drop_address='Bharatpur',
        )

        self.assertEqual(result['distance_km'], Decimal('156.80'))
        self.assertEqual(mock_geocode.call_count, 2)

    @patch('apps.bookings.distance_calculator.calculate_driving_distance')
    def test_with_coordinates(self, mock_distance):
        """Skips geocoding when coordinates provided."""
        mock_distance.return_value = Decimal('156.80')

        result = get_distance_between_locations(
            pickup_address='Jaipur',
            drop_address='Bharatpur',
            pickup_lat=Decimal('26.9124'),
            pickup_lng=Decimal('75.7873'),
            drop_lat=Decimal('27.2152'),
            drop_lng=Decimal('77.4891'),
        )

        self.assertEqual(result['distance_km'], Decimal('156.80'))

    @patch('apps.bookings.distance_calculator.calculate_driving_distance')
    @patch('apps.bookings.distance_calculator.geocode_address')
    def test_distance_exceeds_max(self, mock_geocode, mock_distance):
        """Distance > 5000 km raises ValueError."""
        mock_geocode.side_effect = [
            (Decimal('26.9124'), Decimal('75.7873')),
            (Decimal('40.7128'), Decimal('-74.0060')),
        ]
        mock_distance.return_value = Decimal('12000.00')

        with self.assertRaises(ValueError) as ctx:
            get_distance_between_locations(
                pickup_address='Jaipur',
                drop_address='New York',
            )
        self.assertIn('5,000 km', str(ctx.exception))


# ═══════════════════════════════════════════════════════════════
#  API ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)
class CalculatePriceAPITest(APITestCase):
    """Test POST /api/v1/bookings/calculate-price/ endpoint."""

    def setUp(self):
        self.customer, self.operator = _create_test_users()
        self.bus = _create_test_bus(self.operator)
        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)
        self.url = '/api/v1/bookings/calculate-price/'

    def test_calculate_price_with_estimated_km(self):
        """Calculate price using client-provided estimated_km (no OSRM call)."""
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur, Rajasthan',
            'drop_location': 'Bharatpur, Rajasthan',
            'trip_type': 'one_way',
            'pickup_date': '2026-03-15',
            'estimated_km': '156.80',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('base_fare', data)
        self.assertIn('total', data)
        self.assertIn('driver_charge', data)
        self.assertIn('toll_estimate', data)
        self.assertIn('platform_fee', data)
        self.assertEqual(data['trip_days'], 1)
        # base_fare = max(3000, 18.50 * 156.80) = 3000
        self.assertEqual(data['base_fare'], '3000.00')

    @patch('apps.bookings.distance_calculator.get_distance_between_locations')
    def test_calculate_price_with_osrm(self, mock_distance):
        """Calculate price using OSRM distance when estimated_km not provided."""
        mock_distance.return_value = {
            'distance_km': Decimal('156.80'),
            'pickup_lat': Decimal('26.9124'),
            'pickup_lng': Decimal('75.7873'),
            'drop_lat': Decimal('27.2152'),
            'drop_lng': Decimal('77.4891'),
        }

        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur, Rajasthan',
            'drop_location': 'Bharatpur, Rajasthan',
            'trip_type': 'one_way',
            'pickup_date': '2026-03-15',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        mock_distance.assert_called_once()

    def test_calculate_price_round_trip(self):
        """Round trip doubles effective distance."""
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'round_trip',
            'pickup_date': '2026-03-15',
            'return_date': '2026-03-16',
            'estimated_km': '156.80',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['effective_distance_km'], '313.60')
        self.assertEqual(data['trip_days'], 2)

    def test_calculate_price_multi_day(self):
        """Multi-day adds driver + night charges."""
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Udaipur',
            'trip_type': 'multi_day',
            'pickup_date': '2026-03-15',
            'return_date': '2026-03-17',
            'estimated_km': '400.00',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['trip_days'], 3)
        self.assertEqual(data['night_count'], 2)
        # driver = 500 * 3 = 1500
        self.assertEqual(data['driver_charge'], '1500.00')
        # night = 1000 * 2 = 2000
        self.assertEqual(data['night_charge'], '2000.00')

    def test_unauthenticated_rejected(self):
        """Unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'one_way',
            'pickup_date': '2026-03-15',
            'estimated_km': '156.80',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_round_trip_requires_return_date(self):
        """Round trip without return_date is rejected."""
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'round_trip',
            'pickup_date': '2026-03-15',
            'estimated_km': '156.80',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_return_date_before_pickup_rejected(self):
        """Return date before pickup is rejected."""
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'round_trip',
            'pickup_date': '2026-03-15',
            'return_date': '2026-03-14',
            'estimated_km': '156.80',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_missing_bus_rejected(self):
        """Missing bus field is rejected."""
        response = self.client.post(self.url, {
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'one_way',
            'pickup_date': '2026-03-15',
            'estimated_km': '156.80',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('apps.bookings.distance_calculator.get_distance_between_locations')
    def test_osrm_failure_returns_400(self, mock_distance):
        """OSRM failure returns 400 with error message."""
        mock_distance.side_effect = ValueError('Distance calculation service is temporarily unavailable.')

        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'one_way',
            'pickup_date': '2026-03-15',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_response_includes_bus_info(self):
        """Response includes bus pricing details."""
        response = self.client.post(self.url, {
            'bus': str(self.bus.id),
            'pickup_location': 'Jaipur',
            'drop_location': 'Bharatpur',
            'trip_type': 'one_way',
            'pickup_date': '2026-03-15',
            'estimated_km': '100',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('bus', data)
        self.assertEqual(data['bus']['name'], 'Price Test Bus')
        self.assertEqual(data['bus']['price_per_km'], '18.50')
