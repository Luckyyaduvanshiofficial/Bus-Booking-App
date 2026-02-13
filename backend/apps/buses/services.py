"""Business logic for bus management.

All multi-step operations use @transaction.atomic.
Raises ValidationError for invalid data.
"""

from __future__ import annotations

import datetime
from typing import Optional

from django.db import transaction
from django.db.models import QuerySet
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
    ) -> QuerySet[Bus]:
        """Search for available buses matching the given criteria.

        Args:
            date: Date string in YYYY-MM-DD format.
            passengers: Minimum passenger capacity required.
            city: City to filter by (case-insensitive contains).
            bus_type: Bus type filter.

        Returns:
            QuerySet of matching Bus objects.

        Raises:
            ValidationError: If date format is invalid.
        """
        qs = Bus.objects.filter(
            is_active=True, approval_status='approved',
        ).select_related('operator').prefetch_related('photos', 'amenities')

        if passengers:
            qs = qs.filter(seating_capacity__gte=passengers)
        if city:
            qs = qs.filter(base_city__icontains=city)
        if bus_type:
            qs = qs.filter(bus_type=bus_type)

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
            blocked_ids = AvailabilityBlock.objects.filter(
                blocked_date=search_date,
            ).values_list('bus_id', flat=True)
            qs = qs.exclude(id__in=blocked_ids)

        # Error Code: BUS-SERV-NOTFOUND-001
        # Message: No buses available for selected criteria
        # Cause: No matching buses
        # Solution: Try different date/route
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
            bus.approval_status = 'approved'
        elif action == 'reject':
            bus.approval_status = 'rejected'
        else:
            # Error Code: BUS-SERV-VAL-001
            # Message: Invalid bus approval action
            # Cause: action parameter is not 'approve' or 'reject'
            # Solution: Pass action='approve' or action='reject'
            raise ValidationError(
                'action must be approve or reject.',
                code='BUS-SERV-VAL-001',
            )

        bus.save(update_fields=['approval_status'])
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
