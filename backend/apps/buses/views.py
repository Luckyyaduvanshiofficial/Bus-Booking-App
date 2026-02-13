from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import datetime

from .models import Bus, BusPhoto, BusAmenity, AvailabilityBlock
from .serializers import (
    BusListSerializer, BusDetailSerializer, BusCreateUpdateSerializer,
    BusPhotoSerializer, BusAmenitySerializer,
    AvailabilityBlockSerializer, AvailabilityBlockCreateSerializer,
)
from apps.users.permissions import IsOperator, IsOperatorOrAdmin, IsAdmin


# ═══════════════════════════════════════════════════════════════
#  BUS
# ═══════════════════════════════════════════════════════════════

class BusViewSet(viewsets.ModelViewSet):
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

    def get_queryset(self):
        qs = Bus.objects.filter(is_active=True)

        # Public sees only approved buses
        if not self.request.user.is_authenticated or self.request.user.role == 'customer':
            qs = qs.filter(is_approved=True)

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

        # City filter (uses base_city field now)
        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(base_city__icontains=city)

        return qs

    def perform_create(self, serializer):
        if self.request.user.role != 'operator':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only operators can create buses.")
        serializer.save(operator=self.request.user)

    # ── Search (POST) ────────────────────────────────────────

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def search(self, request):
        """Advanced search: filter by date availability, passengers, city."""
        date_str = request.data.get('date')
        passengers = request.data.get('passengers')
        city = request.data.get('city')
        bus_type = request.data.get('bus_type')

        qs = Bus.objects.filter(is_active=True, is_approved=True)

        if passengers:
            qs = qs.filter(seating_capacity__gte=passengers)
        if city:
            qs = qs.filter(base_city__icontains=city)
        if bus_type:
            qs = qs.filter(bus_type=bus_type)

        # Exclude buses blocked on the requested date
        if date_str:
            try:
                search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                blocked_ids = AvailabilityBlock.objects.filter(
                    blocked_date=search_date,
                ).values_list('bus_id', flat=True)
                qs = qs.exclude(id__in=blocked_ids)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = BusListSerializer(qs, many=True)
        return Response(serializer.data)

    # ── Operator's own buses ─────────────────────────────────

    @action(detail=False, methods=['get'], permission_classes=[IsOperator])
    def my_buses(self, request):
        buses = Bus.objects.filter(operator=request.user)
        serializer = BusListSerializer(buses, many=True)
        return Response(serializer.data)

    # ── Admin approval ───────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        bus = self.get_object()
        act = request.data.get('action')  # 'approve' | 'reject'
        if act == 'approve':
            bus.is_approved = True
            bus.approval_status = 'approved'
        elif act == 'reject':
            bus.is_approved = False
            bus.approval_status = 'rejected'
        else:
            return Response({'error': 'action must be approve or reject'},
                            status=status.HTTP_400_BAD_REQUEST)
        bus.save(update_fields=['is_approved', 'approval_status'])
        return Response(BusDetailSerializer(bus).data)


# ═══════════════════════════════════════════════════════════════
#  BUS PHOTOS
# ═══════════════════════════════════════════════════════════════

class BusPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = BusPhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BusPhoto.objects.filter(bus_id=self.kwargs.get('bus_id'))

    def perform_create(self, serializer):
        bus = Bus.objects.get(id=self.kwargs['bus_id'])
        if bus.operator != self.request.user and self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not your bus.")
        serializer.save(bus=bus)


# ═══════════════════════════════════════════════════════════════
#  BUS AMENITIES
# ═══════════════════════════════════════════════════════════════

class BusAmenityViewSet(viewsets.ModelViewSet):
    serializer_class = BusAmenitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BusAmenity.objects.filter(bus_id=self.kwargs.get('bus_id'))

    def perform_create(self, serializer):
        bus = Bus.objects.get(id=self.kwargs['bus_id'])
        if bus.operator != self.request.user and self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not your bus.")
        serializer.save(bus=bus)


# ═══════════════════════════════════════════════════════════════
#  AVAILABILITY BLOCKS
# ═══════════════════════════════════════════════════════════════

class AvailabilityBlockViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilityBlockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AvailabilityBlock.objects.filter(bus_id=self.kwargs.get('bus_id'))

    def get_serializer_class(self):
        if self.action == 'create':
            return AvailabilityBlockCreateSerializer
        return AvailabilityBlockSerializer

    def perform_create(self, serializer):
        bus = Bus.objects.get(id=self.kwargs['bus_id'])
        if bus.operator != self.request.user and self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not your bus.")
        serializer.save(bus=bus)
