"""Business logic for bus management.

All multi-step operations use @transaction.atomic.
Raises ValidationError for invalid data.
"""

from __future__ import annotations

import datetime
from typing import Optional

from django.db import transaction
from django.db.models import Count, QuerySet
from rest_framework.exceptions import ValidationError

from apps.buses.models import AvailabilityBlock, Bus, BusPhoto, BusAmenity
from apps.users.models import CustomUser


class BusService:
    """Handles bus search, creation, and approval."""

    @staticmethod
    def search_available(
        *,
        date: Optional[str] = None,
        passengers: Optional[int] = None,
        city: Optional[str] = None,
        bus_type: Optional[str] = None,
        ac_type: Optional[str] = None,
        fuel_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        amenities: Optional[list[str]] = None,
        sort_by: Optional[str] = None,
    ) -> QuerySet[Bus]:
        """Search for available buses matching the given criteria.

        Args:
            date: Date string in YYYY-MM-DD format.
            passengers: Minimum passenger capacity required.
            city: City to filter by (case-insensitive contains).
            bus_type: Bus type filter.
            ac_type: AC type filter (ac/non_ac).
            fuel_type: Fuel type filter (diesel/cng/electric).
            min_price: Minimum price per km.
            max_price: Maximum price per km.
            min_rating: Minimum rating (1.0-5.0).
            amenities: List of amenity names to filter by (bus must have ALL).
            sort_by: Sort field - 'price_asc', 'price_desc', 'rating_desc', 
                     'capacity_desc', 'newest'.

        Returns:
            QuerySet of matching Bus objects.

        Raises:
            ValidationError: If date format is invalid.
        """
        qs = Bus.objects.filter(
            is_active=True,
            approval_status=Bus.ApprovalStatus.APPROVED,
            operator__is_verified=True,
            operator__is_active=True,
        ).select_related('operator').prefetch_related('photos', 'amenities')

        # Basic filters
        if passengers:
            qs = qs.filter(seating_capacity__gte=passengers)
        if city:
            qs = qs.filter(base_city__icontains=city)
        if bus_type:
            qs = qs.filter(bus_type=bus_type)
        if ac_type:
            qs = qs.filter(ac_type=ac_type)
        if fuel_type:
            qs = qs.filter(fuel_type=fuel_type)

        # Price range filters
        if min_price is not None:
            qs = qs.filter(price_per_km__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price_per_km__lte=max_price)

        # Rating filter
        if min_rating is not None:
            qs = qs.filter(rating_avg__gte=min_rating)

        # Amenities filter (bus must have ALL specified amenities)
        if amenities:
            amenities = list(set(amenities))  # Deduplicate
            qs = qs.filter(
                amenities__amenity__in=amenities,
            ).annotate(
                matching_amenities=Count('amenities', distinct=True),
            ).filter(
                matching_amenities=len(amenities),
            )

        # Date availability filter
        if date:
            try:
                search_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                # Error Code: COM-UTILS-VAL-001
                # Message: Invalid date format
                # Cause: Date string does not match YYYY-MM-DD pattern
                # Solution: Provide date in YYYY-MM-DD format
                raise ValidationError(
                    'Invalid date format. Use YYYY-MM-DD.',
                    code='COM-UTILS-VAL-001',
                )
            
            # Validate date is not in the past
            if search_date < datetime.date.today():
                # Error Code: BUS-SERV-VAL-002
                # Message: Cannot search for past dates
                # Cause: Provided date is before today
                # Solution: Provide current or future date
                raise ValidationError(
                    'Cannot search for buses on past dates.',
                    code='BUS-SERV-VAL-002',
                )
            
            blocked_ids = AvailabilityBlock.objects.filter(
                blocked_date=search_date,
            ).values_list('bus_id', flat=True)
            qs = qs.exclude(id__in=blocked_ids)

        # Sorting
        if sort_by == 'price_asc':
            qs = qs.order_by('price_per_km')
        elif sort_by == 'price_desc':
            qs = qs.order_by('-price_per_km')
        elif sort_by == 'rating_desc':
            qs = qs.order_by('-rating_avg')
        elif sort_by == 'capacity_desc':
            qs = qs.order_by('-seating_capacity')
        elif sort_by == 'newest':
            qs = qs.order_by('-created_at')
        else:
            # Default: highest rated first, then newest
            qs = qs.order_by('-rating_avg', '-created_at')

        # Error Code: BUS-SERV-NOTFOUND-001
        # Message: No buses available for selected criteria
        # Cause: No matching buses
        # Solution: Try different filters or date
        # (Returns empty queryset; calling code should handle empty results)

        return qs

    @staticmethod
    @transaction.atomic
    def approve_bus(
        *,
        bus: Bus,
        action: str,
    ) -> Bus:
        """Admin approves or rejects a bus.

        Args:
            bus: The bus to approve/reject.
            action: 'approve' or 'reject'.

        Returns:
            The updated Bus instance.

        Raises:
            ValidationError: If action is invalid.
        """
        if action == 'approve':
            bus.approval_status = Bus.ApprovalStatus.APPROVED
        elif action == 'reject':
            bus.approval_status = Bus.ApprovalStatus.REJECTED
        else:
            # Error Code: BUS-SERV-VAL-001
            # Message: Invalid bus approval action
            # Cause: action parameter is not 'approve' or 'reject'
            # Solution: Pass action='approve' or action='reject'
            raise ValidationError(
                'action must be approve or reject.',
                code='BUS-SERV-VAL-001',
            )

        bus.save(update_fields=['approval_status', 'updated_at'])
        return bus

    @staticmethod
    @transaction.atomic
    def block_date(
        *,
        bus: Bus,
        blocked_date: 'datetime.date',
        block_reason: str = 'personal',
    ) -> AvailabilityBlock:
        """Block a date for a bus.

        Args:
            bus: The bus to block.
            blocked_date: The date to block.
            block_reason: Reason for blocking.

        Returns:
            The created AvailabilityBlock.

        Raises:
            ValidationError: If date is already blocked.
        """
        if AvailabilityBlock.objects.filter(
            bus=bus, blocked_date=blocked_date,
        ).exists():
            # Error Code: BUS-SERV-CONFLICT-001
            # Message: Bus already blocked on this date
            # Cause: Duplicate availability block
            # Solution: Check existing blocks before creating
            raise ValidationError(
                'Bus is already blocked on this date.',
                code='BUS-SERV-CONFLICT-001',
            )
        return AvailabilityBlock.objects.create(
            bus=bus,
            blocked_date=blocked_date,
            block_reason=block_reason,
        )
