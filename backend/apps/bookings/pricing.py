"""Pricing calculator for bus charter bookings.

Implements the charter pricing formula:
    total = max(base_price, price_per_km × distance)
          + (driver_charge × trip_days)
          + (night_halt_charge × max(0, trip_days - 1))
          + toll_estimate (2% of base fare)
          + platform_fee (max(₹199, 3% of subtotal))

All calculations use Decimal to avoid floating-point precision loss.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

logger = logging.getLogger(__name__)

TWO_PLACES = Decimal('0.01')

# Platform fee constants
MIN_PLATFORM_FEE = Decimal('199.00')
PLATFORM_FEE_RATE = Decimal('0.03')

# Toll estimate rate (2% of base fare)
TOLL_ESTIMATE_RATE = Decimal('0.02')

# Commission defaults
DEFAULT_COMMISSION_RATE = Decimal('10.00')


def calculate_trip_days(
    pickup_date: date,
    return_date: Optional[date],
    trip_type: str,
) -> int:
    """Calculate number of trip days from dates and trip type.

    Args:
        pickup_date: Trip start date.
        return_date: Trip end date (None for one-way).
        trip_type: One of 'one_way', 'round_trip', 'multi_day'.

    Returns:
        Number of trip days (minimum 1).
    """
    if trip_type == 'one_way' or not return_date:
        return 1

    days = (return_date - pickup_date).days
    return max(1, days + 1)


def calculate_booking_price(
    *,
    distance_km: Decimal,
    base_price: Decimal,
    price_per_km: Decimal,
    driver_charge_per_day: Decimal,
    night_halt_charge: Decimal,
    trip_days: int,
    trip_type: str,
    commission_rate: Optional[Decimal] = None,
) -> dict:
    """Calculate full price breakdown for a bus charter booking.

    Formula:
        base_fare = max(base_price, price_per_km × distance_km)
        For round_trip: distance doubles (return journey)
        driver_total = driver_charge_per_day × trip_days
        night_total = night_halt_charge × max(0, trip_days - 1)
        toll_estimate = base_fare × 2%
        subtotal = base_fare + driver_total + night_total + toll_estimate
        platform_fee = max(₹199, subtotal × 3%)
        total = subtotal + platform_fee

    Args:
        distance_km: One-way driving distance in km.
        base_price: Minimum charge for the bus.
        price_per_km: Per-kilometer rate.
        driver_charge_per_day: Driver daily charge.
        night_halt_charge: Per-night halt charge.
        trip_days: Number of trip days.
        trip_type: One of 'one_way', 'round_trip', 'multi_day'.
        commission_rate: Platform commission percentage (default 10%).

    Returns:
        Dict with complete price breakdown.
    """
    effective_distance = distance_km
    if trip_type == 'round_trip':
        effective_distance = distance_km * Decimal('2')

    # Base fare: max of minimum charge or distance-based price
    distance_charge = (price_per_km * effective_distance).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )
    base_fare = max(base_price, distance_charge)

    # Driver charge: per day
    driver_total = (driver_charge_per_day * Decimal(str(trip_days))).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )

    # Night halt: only for multi-day trips (trip_days - 1 nights)
    night_count = max(0, trip_days - 1)
    night_total = (night_halt_charge * Decimal(str(night_count))).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )

    # Toll estimate: 2% of base fare
    toll_estimate = (base_fare * TOLL_ESTIMATE_RATE).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )

    # Subtotal before platform fee
    subtotal = base_fare + driver_total + night_total + toll_estimate

    # Platform fee: max(₹199, 3% of subtotal)
    percentage_fee = (subtotal * PLATFORM_FEE_RATE).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )
    platform_fee = max(MIN_PLATFORM_FEE, percentage_fee)

    # Total
    total = (subtotal + platform_fee).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )

    # Commission (operator pays platform)
    rate = commission_rate if commission_rate is not None else DEFAULT_COMMISSION_RATE
    commission_amount = (subtotal * rate / Decimal('100')).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )
    operator_payout = (subtotal - commission_amount).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP,
    )

    return {
        'distance_km': distance_km,
        'effective_distance_km': effective_distance,
        'base_fare': base_fare,
        'driver_charge': driver_total,
        'night_charge': night_total,
        'toll_estimate': toll_estimate,
        'subtotal': subtotal,
        'platform_fee': platform_fee,
        'total': total,
        'trip_days': trip_days,
        'night_count': night_count,
        'commission_rate': rate,
        'commission_amount': commission_amount,
        'operator_payout': operator_payout,
    }
