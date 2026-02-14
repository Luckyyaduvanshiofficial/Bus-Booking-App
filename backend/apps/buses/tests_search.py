"""Tests for enhanced bus search and filter functionality."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.buses.models import AvailabilityBlock, Bus, BusAmenity
from apps.buses.services import BusService

User = get_user_model()


class BusSearchServiceTest(TestCase):
    """Test BusService.search_available with enhanced filters."""

    def setUp(self):
        """Create test data: operator, buses with different attributes."""
        self.operator = User.objects.create_user(
            '9876543210',  # phone (USERNAME_FIELD) as positional
            '9876543210',  # username (REQUIRED_FIELDS) as positional
            email='operator@test.com',
            name='Test Operator',
            role='operator',
            is_verified=True,
            is_active=True,
        )

        # Bus 1: Cheap, low capacity, Jaipur
        self.bus1 = Bus.objects.create(
            operator=self.operator,
            name='Budget Express',
            registration_number='RJ01AB1111',
            bus_type='medium_bus',
            ac_type='non_ac',
            fuel_type='diesel',
            seating_capacity=30,
            base_city='Jaipur',
            price_per_km=Decimal('15.00'),
            base_price=Decimal('2000.00'),
            driver_charge=Decimal('400.00'),
            night_charge=Decimal('800.00'),
            rating_avg=Decimal('3.5'),
            approval_status='approved',
            is_active=True,
        )
        BusAmenity.objects.create(bus=self.bus1, amenity='wifi')

        # Bus 2: Mid-range, good rating, Delhi
        self.bus2 = Bus.objects.create(
            operator=self.operator,
            name='Comfort Travels',
            registration_number='DL02CD2222',
            bus_type='luxury_coach',
            ac_type='ac',
            fuel_type='diesel',
            seating_capacity=45,
            base_city='Delhi',
            price_per_km=Decimal('20.00'),
            base_price=Decimal('3000.00'),
            driver_charge=Decimal('500.00'),
            night_charge=Decimal('1000.00'),
            rating_avg=Decimal('4.5'),
            approval_status='approved',
            is_active=True,
        )
        BusAmenity.objects.create(bus=self.bus2, amenity='wifi')
        BusAmenity.objects.create(bus=self.bus2, amenity='charging_points')

        # Bus 3: Premium, high capacity, Jaipur
        self.bus3 = Bus.objects.create(
            operator=self.operator,
            name='Luxury Coach',
            registration_number='RJ03EF3333',
            bus_type='luxury_coach',
            ac_type='ac',
            fuel_type='cng',
            seating_capacity=50,
            base_city='Jaipur',
            price_per_km=Decimal('30.00'),
            base_price=Decimal('5000.00'),
            driver_charge=Decimal('600.00'),
            night_charge=Decimal('1500.00'),
            rating_avg=Decimal('4.8'),
            approval_status='approved',
            is_active=True,
        )
        BusAmenity.objects.create(bus=self.bus3, amenity='wifi')
        BusAmenity.objects.create(bus=self.bus3, amenity='charging_points')

        # Bus 4: Not approved (should never appear)
        self.bus4 = Bus.objects.create(
            operator=self.operator,
            name='Pending Bus',
            registration_number='RJ04GH4444',
            bus_type='luxury_coach',
            ac_type='ac',
            fuel_type='diesel',
            seating_capacity=40,
            base_city='Jaipur',
            price_per_km=Decimal('18.00'),
            approval_status='pending',
            is_active=True,
        )

    def test_search_no_filters_returns_all_approved(self):
        """Search with no filters returns all approved buses."""
        result = BusService.search_available()
        self.assertEqual(result.count(), 3)
        self.assertIn(self.bus1, result)
        self.assertIn(self.bus2, result)
        self.assertIn(self.bus3, result)
        self.assertNotIn(self.bus4, result)

    def test_filter_by_city(self):
        """Filter by city returns only buses from that city."""
        result = BusService.search_available(city='Jaipur')
        self.assertEqual(result.count(), 2)
        self.assertIn(self.bus1, result)
        self.assertIn(self.bus3, result)

    def test_filter_by_city_case_insensitive(self):
        """City filter is case-insensitive."""
        result = BusService.search_available(city='jaipur')
        self.assertEqual(result.count(), 2)

    def test_filter_by_passengers(self):
        """Filter by passengers returns buses with sufficient capacity."""
        result = BusService.search_available(passengers=40)
        self.assertEqual(result.count(), 2)
        self.assertIn(self.bus2, result)
        self.assertIn(self.bus3, result)
        self.assertNotIn(self.bus1, result)  # Only 30 seats

    def test_filter_by_ac_type(self):
        """Filter by AC type returns only AC or non-AC buses."""
        result = BusService.search_available(ac_type='ac')
        self.assertEqual(result.count(), 2)
        self.assertIn(self.bus2, result)
        self.assertIn(self.bus3, result)

    def test_filter_by_fuel_type(self):
        """Filter by fuel type returns matching buses."""
        result = BusService.search_available(fuel_type='cng')
        self.assertEqual(result.count(), 1)
        self.assertIn(self.bus3, result)

    def test_filter_by_price_range(self):
        """Filter by price range returns buses within range."""
        result = BusService.search_available(min_price=18.0, max_price=25.0)
        self.assertEqual(result.count(), 1)
        self.assertIn(self.bus2, result)  # 20.00 per km

    def test_filter_by_min_rating(self):
        """Filter by minimum rating returns highly-rated buses."""
        result = BusService.search_available(min_rating=4.0)
        self.assertEqual(result.count(), 2)
        self.assertIn(self.bus2, result)
        self.assertIn(self.bus3, result)

    def test_filter_by_single_amenity(self):
        """Filter by single amenity returns buses with that amenity."""
        result = BusService.search_available(amenities=['wifi'])
        self.assertEqual(result.count(), 3)  # All have WiFi

    def test_filter_by_multiple_amenities(self):
        """Filter by multiple amenities returns buses with ALL amenities."""
        result = BusService.search_available(amenities=['wifi', 'charging_points'])
        self.assertEqual(result.count(), 2)
        self.assertIn(self.bus2, result)
        self.assertIn(self.bus3, result)
        self.assertNotIn(self.bus1, result)  # Only has WiFi

    def test_filter_by_date_availability(self):
        """Filter by date excludes buses blocked on that date."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        # Block bus1 for tomorrow
        AvailabilityBlock.objects.create(
            bus=self.bus1,
            blocked_date=date.today() + timedelta(days=1),
            block_reason='booked_platform',
        )
        
        result = BusService.search_available(date=tomorrow)
        self.assertEqual(result.count(), 2)
        self.assertIn(self.bus2, result)
        self.assertIn(self.bus3, result)
        self.assertNotIn(self.bus1, result)

    def test_filter_past_date_raises_error(self):
        """Searching for past date raises ValidationError."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        with self.assertRaises(Exception) as ctx:
            BusService.search_available(date=yesterday)
        self.assertIn('BUS-SERV-VAL-002', str(ctx.exception))

    def test_invalid_date_format_raises_error(self):
        """Invalid date format raises ValidationError."""
        with self.assertRaises(Exception) as ctx:
            BusService.search_available(date='2026-13-45')
        self.assertIn('COM-UTILS-VAL-001', str(ctx.exception))

    def test_sort_by_price_asc(self):
        """Sort by price ascending returns cheapest first."""
        result = list(BusService.search_available(sort_by='price_asc'))
        self.assertEqual(result[0], self.bus1)  # 15.00
        self.assertEqual(result[1], self.bus2)  # 20.00
        self.assertEqual(result[2], self.bus3)  # 30.00

    def test_sort_by_price_desc(self):
        """Sort by price descending returns most expensive first."""
        result = list(BusService.search_available(sort_by='price_desc'))
        self.assertEqual(result[0], self.bus3)  # 30.00
        self.assertEqual(result[1], self.bus2)  # 20.00
        self.assertEqual(result[2], self.bus1)  # 15.00

    def test_sort_by_rating_desc(self):
        """Sort by rating descending returns highest rated first."""
        result = list(BusService.search_available(sort_by='rating_desc'))
        self.assertEqual(result[0], self.bus3)  # 4.8
        self.assertEqual(result[1], self.bus2)  # 4.5
        self.assertEqual(result[2], self.bus1)  # 3.5

    def test_sort_by_capacity_desc(self):
        """Sort by capacity descending returns largest first."""
        result = list(BusService.search_available(sort_by='capacity_desc'))
        self.assertEqual(result[0], self.bus3)  # 50
        self.assertEqual(result[1], self.bus2)  # 45
        self.assertEqual(result[2], self.bus1)  # 30

    def test_combined_filters(self):
        """Multiple filters work together correctly."""
        result = BusService.search_available(
            city='Jaipur',
            passengers=40,
            min_rating=4.0,
            amenities=['wifi', 'charging_points'],
            sort_by='price_desc',
        )
        self.assertEqual(result.count(), 1)
        self.assertIn(self.bus3, result)


class BusSearchAPITest(TestCase):
    """Test POST /api/v1/buses/search/ endpoint."""

    def setUp(self):
        """Set up API client and test data."""
        self.client = APIClient()
        
        self.operator = User.objects.create_user(
            '9876543210',  # phone (USERNAME_FIELD) as positional
            '9876543210',  # username (REQUIRED_FIELDS) as positional
            email='operator@test.com',
            name='Test Operator',
            role='operator',
            is_verified=True,
            is_active=True,
        )

        # Create 25 buses for pagination testing
        for i in range(25):
            Bus.objects.create(
                operator=self.operator,
                name=f'Bus {i+1}',
                registration_number=f'RJ01AB{i+1:04d}',
                bus_type='luxury_coach',
                ac_type='ac',
                fuel_type='diesel',
                seating_capacity=40,
                base_city='Jaipur',
                price_per_km=Decimal('18.00') + Decimal(i),
                base_price=Decimal('2500.00'),
                approval_status='approved',
                is_active=True,
            )

    def test_search_empty_body_returns_all(self):
        """Empty search body returns all approved buses."""
        response = self.client.post('/api/v1/buses/search/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 20)  # Paginated

    def test_search_with_filters(self):
        """Search with filters returns filtered results."""
        response = self.client.post(
            '/api/v1/buses/search/',
            {
                'city': 'Jaipur',
                'passengers': 40,
                'min_price': 20.0,
                'max_price': 30.0,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        # Should return buses with price 20-30 (indices 2-12 = 11 buses)
        self.assertGreater(len(response.data['results']), 0)

    def test_search_returns_pagination_metadata(self):
        """Search response includes pagination metadata."""
        response = self.client.post('/api/v1/buses/search/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('count', response.data)  # Total count
        self.assertIn('next', response.data)  # Next page URL
        self.assertIn('previous', response.data)  # Previous page URL
        self.assertIn('results', response.data)  # Results array
        self.assertEqual(response.data['count'], 25)

    def test_search_pagination_page_2(self):
        """Can fetch second page of results."""
        response = self.client.post(
            '/api/v1/buses/search/?page=2',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 5)  # Remaining 5 buses

    def test_search_with_sort_by(self):
        """Search respects sort_by parameter."""
        response = self.client.post(
            '/api/v1/buses/search/',
            {'sort_by': 'price_asc'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        # First bus should have lowest price
        self.assertEqual(results[0]['name'], 'Bus 1')

    def test_search_invalid_date_returns_400(self):
        """Search with invalid date returns 400."""
        response = self.client.post(
            '/api/v1/buses/search/',
            {'date': 'invalid-date'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('COM-UTILS-VAL-001', str(response.data))

    def test_search_past_date_returns_400(self):
        """Search with past date returns 400."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/v1/buses/search/',
            {'date': yesterday},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('BUS-SERV-VAL-002', str(response.data))

    def test_search_unauthenticated_allowed(self):
        """Search endpoint allows unauthenticated users."""
        # Don't authenticate
        response = self.client.post('/api/v1/buses/search/', {}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_search_returns_bus_details(self):
        """Search results include bus details (name, capacity, price, etc.)."""
        response = self.client.post('/api/v1/buses/search/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        first_bus = response.data['results'][0]
        self.assertIn('id', first_bus)
        self.assertIn('name', first_bus)
        self.assertIn('seating_capacity', first_bus)
        self.assertIn('price_per_km', first_bus)
        self.assertIn('base_city', first_bus)
        self.assertIn('rating_avg', first_bus)
