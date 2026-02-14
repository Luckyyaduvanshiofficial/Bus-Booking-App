"""Bus ViewSets – thin controllers.

All business logic is delegated to services.py.
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.users.models import CustomUser
from apps.users.permissions import IsAdmin, IsOperator

from .models import AvailabilityBlock, Bus, BusAmenity, BusPhoto
from .serializers import (
    AvailabilityBlockCreateSerializer,
    AvailabilityBlockSerializer,
    BusAmenitySerializer,
    BusCreateUpdateSerializer,
    BusDetailSerializer,
    BusListSerializer,
    BusPhotoSerializer,
)
from .services import BusService


# ═══════════════════════════════════════════════════════════════
#  BUS OWNERSHIP MIXIN
# ═══════════════════════════════════════════════════════════════


class BusOwnershipMixin:
    """Shared bus lookup and permission check for photo/amenity/block viewsets."""

    def get_bus(self) -> Bus:
        """Look up the bus by URL kwarg, returning 404 if not found."""
        return get_object_or_404(
            Bus.objects.select_related('operator'),
            id=self.kwargs['bus_id'],
        )

    def check_bus_permission(self, bus: Bus) -> None:
        """Raise PermissionDenied if user is not the bus owner or admin."""
        if (
            bus.operator != self.request.user
            and self.request.user.role != CustomUser.Role.ADMIN
        ):
            # Error Code: BUS-VIEWS-PERM-002
            # Message: Not authorized to modify this bus
            # Cause: User is not the bus owner or an admin
            # Solution: Only the bus operator or admin can perform this action
            raise PermissionDenied(
                "Not your bus.",
                code='BUS-VIEWS-PERM-002',
            )

    def check_object_bus_permission(self, obj) -> None:
        """Authorize mutations on nested objects using their related bus."""
        bus = getattr(obj, 'bus', None) or self.get_bus()
        self.check_bus_permission(bus)

    def scope_queryset_to_owner_or_admin(self, queryset: QuerySet) -> QuerySet:
        """Restrict nested management endpoints to bus owner/admin only."""
        user = self.request.user
        if user.role == CustomUser.Role.ADMIN:
            return queryset
        return queryset.filter(bus__operator=user)


# ═══════════════════════════════════════════════════════════════
#  BUS
# ═══════════════════════════════════════════════════════════════


class BusViewSet(BusOwnershipMixin, viewsets.ModelViewSet):
    """Bus CRUD + search and approval endpoints.

    Delegates search and approval logic to BusService.
    """

    queryset = Bus.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['bus_type', 'ac_type', 'fuel_type', 'base_city']
    search_fields = ['name', 'registration_number', 'operator__business_name', 'base_city']
    ordering_fields = ['price_per_km', 'rating_avg', 'created_at', 'seating_capacity']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'search'):
            return [AllowAny()]
        if self.action in ('my_buses',):
            return [IsOperator()]
        if self.action in ('approve',):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BusDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return BusCreateUpdateSerializer
        return BusListSerializer

    def get_queryset(self) -> QuerySet:
        """Filter buses with optimized queries."""
        qs = Bus.objects.filter(
            is_active=True,
        ).select_related('operator').prefetch_related(
            'photos',
            'amenities',
            'availability_blocks',
        )

        # Public sees only approved buses
        if (
            not self.request.user.is_authenticated
            or self.request.user.role == CustomUser.Role.CUSTOMER
        ):
            qs = qs.filter(
                approval_status=Bus.ApprovalStatus.APPROVED,
                operator__is_verified=True,
                operator__is_active=True,
            )

        # Price range
        min_p = self.request.query_params.get('min_price')
        max_p = self.request.query_params.get('max_price')
        if min_p:
            qs = qs.filter(price_per_km__gte=min_p)
        if max_p:
            qs = qs.filter(price_per_km__lte=max_p)

        # Minimum capacity
        cap = self.request.query_params.get('seating_capacity')
        if cap:
            qs = qs.filter(seating_capacity__gte=cap)

        # City filter
        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(base_city__icontains=city)

        return qs

    def perform_create(self, serializer) -> None:
        """Only operators can create buses."""
        user = self.request.user
        if user.role != CustomUser.Role.OPERATOR:
            # Error Code: BUS-VIEWS-PERM-001
            # Message: Only operators can create buses
            # Cause: Non-operator user attempted to create a bus
            # Solution: Ensure user.role == 'operator' before calling
            raise PermissionDenied(
                "Only operators can create buses.",
                code='BUS-VIEWS-PERM-001',
            )
        if not user.is_verified:
            raise PermissionDenied(
                "Your operator account must be verified before creating buses.",
                code='BUS-VIEWS-PERM-003',
            )
        serializer.save(operator=user)

    def perform_update(self, serializer) -> None:
        """Only the bus owner or admin can update a bus."""
        self.check_bus_permission(self.get_object())
        serializer.save()

    def perform_destroy(self, instance) -> None:
        """Only the bus owner or admin can delete a bus."""
        self.check_bus_permission(instance)
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def search(self, request) -> Response:
        """Advanced search: filter by date availability, passengers, city."""
        buses = BusService.search_available(
            date=request.data.get('date'),
            passengers=request.data.get('passengers'),
            city=request.data.get('city'),
            bus_type=request.data.get('bus_type'),
        )
        # Paginate results to prevent OOM on large result sets
        page = self.paginate_queryset(buses)
        if page is not None:
            return self.get_paginated_response(
                BusListSerializer(page, many=True).data,
            )
        return Response(BusListSerializer(buses, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[IsOperator])
    def my_buses(self, request) -> Response:
        """List the authenticated operator's own buses."""
        buses = Bus.objects.filter(
            operator=request.user,
        ).select_related('operator').prefetch_related('photos', 'amenities')
        return Response(BusListSerializer(buses, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None) -> Response:
        """Admin approves or rejects a bus."""
        bus = self.get_object()
        bus = BusService.approve_bus(
            bus=bus,
            action=request.data.get('action', ''),
        )
        return Response(BusDetailSerializer(bus).data)


# ═══════════════════════════════════════════════════════════════
#  BUS PHOTOS
# ═══════════════════════════════════════════════════════════════


class BusPhotoViewSet(BusOwnershipMixin, viewsets.ModelViewSet):
    """Bus photo management."""

    serializer_class = BusPhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Filter photos by bus."""
        queryset = BusPhoto.objects.filter(
            bus_id=self.kwargs.get('bus_id'),
        ).select_related('bus')
        return self.scope_queryset_to_owner_or_admin(queryset)

    def perform_create(self, serializer) -> None:
        """Only the bus owner or admin can add photos."""
        bus = self.get_bus()
        self.check_bus_permission(bus)
        serializer.save(bus=bus)

    def perform_update(self, serializer) -> None:
        """Only the bus owner or admin can update photos."""
        self.check_object_bus_permission(self.get_object())
        serializer.save()

    def perform_destroy(self, instance) -> None:
        """Only the bus owner or admin can delete photos."""
        self.check_object_bus_permission(instance)
        instance.delete()


# ═══════════════════════════════════════════════════════════════
#  BUS AMENITIES
# ═══════════════════════════════════════════════════════════════


class BusAmenityViewSet(BusOwnershipMixin, viewsets.ModelViewSet):
    """Bus amenity management."""

    serializer_class = BusAmenitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Filter amenities by bus."""
        queryset = BusAmenity.objects.filter(
            bus_id=self.kwargs.get('bus_id'),
        ).select_related('bus')
        return self.scope_queryset_to_owner_or_admin(queryset)

    def perform_create(self, serializer) -> None:
        """Only the bus owner or admin can add amenities."""
        bus = self.get_bus()
        self.check_bus_permission(bus)
        serializer.save(bus=bus)

    def perform_update(self, serializer) -> None:
        """Only the bus owner or admin can update amenities."""
        self.check_object_bus_permission(self.get_object())
        serializer.save()

    def perform_destroy(self, instance) -> None:
        """Only the bus owner or admin can delete amenities."""
        self.check_object_bus_permission(instance)
        instance.delete()


# ═══════════════════════════════════════════════════════════════
#  AVAILABILITY BLOCKS
# ═══════════════════════════════════════════════════════════════


class AvailabilityBlockViewSet(BusOwnershipMixin, viewsets.ModelViewSet):
    """Availability block management."""

    serializer_class = AvailabilityBlockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Filter blocks by bus."""
        queryset = AvailabilityBlock.objects.filter(
            bus_id=self.kwargs.get('bus_id'),
        ).select_related('bus', 'booking')
        return self.scope_queryset_to_owner_or_admin(queryset)

    def get_serializer_class(self):
        if self.action == 'create':
            return AvailabilityBlockCreateSerializer
        return AvailabilityBlockSerializer

    def perform_create(self, serializer) -> None:
        """Only the bus owner or admin can block dates."""
        bus = self.get_bus()
        self.check_bus_permission(bus)
        serializer.save(bus=bus)

    def perform_update(self, serializer) -> None:
        """Only the bus owner or admin can update availability blocks."""
        self.check_object_bus_permission(self.get_object())
        serializer.save()

    def perform_destroy(self, instance) -> None:
        """Only the bus owner or admin can delete availability blocks."""
        self.check_object_bus_permission(instance)
        instance.delete()
