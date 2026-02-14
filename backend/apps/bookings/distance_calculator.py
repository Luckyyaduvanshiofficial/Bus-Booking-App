"""Distance calculation using OpenStreetMap services.

Uses Nominatim for geocoding and OSRM for driving distance.
Both are free, no API key required.

Nominatim usage policy: max 1 request/second, cache results.
OSRM demo server: for development only; self-host for production.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Nominatim (geocoding)
NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org'
NOMINATIM_HEADERS = {
    'User-Agent': 'BusBookingPlatform/1.0 (contact@busbooking.in)',
}
GEOCODE_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days

# OSRM (routing)
OSRM_BASE_URL = 'https://router.project-osrm.org'
OSRM_TIMEOUT = 10  # seconds

TWO_PLACES = Decimal('0.01')


def _geocode_cache_key(address: str) -> str:
    """Generate a cache key for a geocoded address."""
    import hashlib
    normalized = address.strip().lower()
    addr_hash = hashlib.md5(normalized.encode('utf-8')).hexdigest()
    return f'geocode:v1:{addr_hash}'


def geocode_address(address: str) -> tuple[Decimal, Decimal]:
    """Convert a text address to latitude/longitude using Nominatim.

    Results are cached for 7 days to respect Nominatim usage policy.

    Args:
        address: Free-text address string (e.g., "Jaipur, Rajasthan").

    Returns:
        Tuple of (latitude, longitude) as Decimal values.

    Raises:
        ValueError: If geocoding fails or no results found.
            Error Code: BOK-SERV-API-002
    """
    if not address or not address.strip():
        # Error Code: BOK-SERV-VAL-014
        # Message: Location address cannot be empty
        # Cause: Empty or whitespace-only address provided
        # Solution: Provide a valid address string
        raise ValueError('Location address cannot be empty')

    cache_key = _geocode_cache_key(address)
    cached = cache.get(cache_key)
    if cached is not None:
        return (Decimal(cached[0]), Decimal(cached[1]))

    try:
        # Nominatim requires max 1 req/sec — brief sleep for safety
        time.sleep(0.2)

        response = requests.get(
            f'{NOMINATIM_BASE_URL}/search',
            params={
                'q': address.strip(),
                'format': 'json',
                'limit': 1,
                'countrycodes': 'in',
            },
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()

    except requests.RequestException as exc:
        # Error Code: BOK-SERV-API-002
        # Message: Geocoding service unavailable
        # Cause: Nominatim API returned an error or timed out
        # Solution: Retry later or provide lat/lng directly
        logger.error(
            'geocoding_api_failure',
            extra={
                'error_code': 'BOK-SERV-API-002',
                'address': address[:100],
                'error': str(exc),
            },
        )
        raise ValueError(
            'Geocoding service is temporarily unavailable. '
            'Please try again or provide coordinates directly.'
        ) from exc

    if not results:
        # Error Code: BOK-SERV-API-002
        # Message: Address not found
        # Cause: Nominatim returned no results for the address
        # Solution: Check spelling or provide a more specific address
        logger.warning(
            'geocoding_no_results',
            extra={
                'error_code': 'BOK-SERV-API-002',
                'address': address[:100],
            },
        )
        raise ValueError(
            f'Could not find location: "{address[:100]}". '
            'Please check the address or provide coordinates.'
        )

    lat = Decimal(results[0]['lat'])
    lng = Decimal(results[0]['lon'])

    cache.set(cache_key, (str(lat), str(lng)), GEOCODE_CACHE_TTL)

    return (lat, lng)


def calculate_driving_distance(
    origin_lat: Decimal,
    origin_lng: Decimal,
    dest_lat: Decimal,
    dest_lng: Decimal,
) -> Decimal:
    """Calculate driving distance between two coordinates using OSRM.

    Args:
        origin_lat: Origin latitude.
        origin_lng: Origin longitude.
        dest_lat: Destination latitude.
        dest_lng: Destination longitude.

    Returns:
        Driving distance in kilometers (Decimal, 2 places).

    Raises:
        ValueError: If OSRM API fails or returns no route.
            Error Code: BOK-SERV-API-001
    """
    # Validate coordinate ranges
    if not (-90 <= origin_lat <= 90) or not (-90 <= dest_lat <= 90):
        # Error Code: BOK-SERV-VAL-015
        # Message: Latitude out of range
        # Cause: Latitude values must be between -90 and 90
        # Solution: Verify coordinate values
        raise ValueError('Latitude must be between -90 and 90 degrees.')
    if not (-180 <= origin_lng <= 180) or not (-180 <= dest_lng <= 180):
        # Error Code: BOK-SERV-VAL-015
        # Message: Longitude out of range
        # Cause: Longitude values must be between -180 and 180
        # Solution: Verify coordinate values
        raise ValueError('Longitude must be between -180 and 180 degrees.')

    try:
        # OSRM expects lng,lat order (not lat,lng)
        url = (
            f'{OSRM_BASE_URL}/route/v1/driving/'
            f'{origin_lng},{origin_lat};{dest_lng},{dest_lat}'
        )
        response = requests.get(
            url,
            params={'overview': 'false', 'alternatives': 'false'},
            timeout=OSRM_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        # Error Code: BOK-SERV-API-001
        # Message: Distance calculation service unavailable
        # Cause: OSRM API returned an error or timed out
        # Solution: Retry later or provide estimated_km manually
        logger.error(
            'osrm_api_failure',
            extra={
                'error_code': 'BOK-SERV-API-001',
                'origin': f'{origin_lat},{origin_lng}',
                'dest': f'{dest_lat},{dest_lng}',
                'error': str(exc),
            },
        )
        raise ValueError(
            'Distance calculation service is temporarily unavailable. '
            'Please try again later.'
        ) from exc

    if data.get('code') != 'Ok' or not data.get('routes'):
        # Error Code: BOK-SERV-API-001
        # Message: No driving route found
        # Cause: OSRM could not find a valid driving route
        # Solution: Verify locations are road-accessible
        logger.warning(
            'osrm_no_route',
            extra={
                'error_code': 'BOK-SERV-API-001',
                'origin': f'{origin_lat},{origin_lng}',
                'dest': f'{dest_lat},{dest_lng}',
                'osrm_code': data.get('code'),
            },
        )
        raise ValueError(
            'No driving route found between the locations. '
            'Please verify both locations are accessible by road.'
        )

    distance_meters = data['routes'][0]['distance']
    distance_km = (Decimal(str(distance_meters)) / Decimal('1000')).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )

    return distance_km


def get_distance_between_locations(
    pickup_address: str,
    drop_address: str,
    pickup_lat: Optional[Decimal] = None,
    pickup_lng: Optional[Decimal] = None,
    drop_lat: Optional[Decimal] = None,
    drop_lng: Optional[Decimal] = None,
) -> dict:
    """Get driving distance between two locations.

    If coordinates are provided, uses them directly. Otherwise,
    geocodes the text addresses first.

    Args:
        pickup_address: Pickup location text.
        drop_address: Drop location text.
        pickup_lat: Optional pre-geocoded pickup latitude.
        pickup_lng: Optional pre-geocoded pickup longitude.
        drop_lat: Optional pre-geocoded drop latitude.
        drop_lng: Optional pre-geocoded drop longitude.

    Returns:
        Dict with distance_km, pickup coords, and drop coords.

    Raises:
        ValueError: If geocoding or distance calculation fails.
    """
    if pickup_lat is None or pickup_lng is None:
        pickup_lat, pickup_lng = geocode_address(pickup_address)
    if drop_lat is None or drop_lng is None:
        drop_lat, drop_lng = geocode_address(drop_address)

    distance_km = calculate_driving_distance(
        origin_lat=pickup_lat,
        origin_lng=pickup_lng,
        dest_lat=drop_lat,
        dest_lng=drop_lng,
    )

    # Validate distance is reasonable
    if distance_km <= 0:
        # Error Code: BOK-SERV-VAL-014
        # Message: Calculated distance must be positive
        # Cause: OSRM returned zero or negative distance
        # Solution: Check that pickup and drop are different locations
        raise ValueError('Distance must be greater than zero.')

    if distance_km > Decimal('5000'):
        # Error Code: BOK-SERV-VAL-014
        # Message: Distance exceeds maximum (5000 km)
        # Cause: Locations are too far apart for a bus charter
        # Solution: Verify pickup and drop locations are correct
        raise ValueError(
            'Distance exceeds the maximum of 5,000 km. '
            'Please verify your locations.'
        )

    return {
        'distance_km': distance_km,
        'pickup_lat': pickup_lat,
        'pickup_lng': pickup_lng,
        'drop_lat': drop_lat,
        'drop_lng': drop_lng,
    }
