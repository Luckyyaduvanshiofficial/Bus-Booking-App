"""Review ViewSets – thin controllers.

All moderation logic is delegated to services.py.
"""

from __future__ import annotations

import uuid as uuid_mod

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdmin

from .models import BusReview, OperatorReview
from .serializers import (
    BusReviewCreateSerializer,
    BusReviewSerializer,
    OperatorReviewSerializer,
)
from .services import ReviewService


# ═══════════════════════════════════════════════════════════════
#  BUS REVIEW
# ═══════════════════════════════════════════════════════════════


class BusReviewViewSet(viewsets.ModelViewSet):
    """Bus review CRUD + moderation.

    Delegates moderation logic to ReviewService.
    """

    serializer_class = BusReviewSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'bus_reviews'):
            return [AllowAny()]
        if self.action in ('moderate',):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return BusReviewCreateSerializer
        return BusReviewSerializer

    def get_queryset(self) -> QuerySet:
        """Admin sees all; public sees only approved reviews."""
        qs = BusReview.objects.select_related('customer', 'bus', 'operator')
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return qs
        return qs.filter(is_approved=True)

    def perform_create(self, serializer) -> None:
        """Attach customer, bus, and operator from validated booking."""
        booking = serializer.validated_data['booking']
        serializer.save(
            customer=self.request.user,
            bus=booking.bus,
            operator=booking.operator,
        )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def bus_reviews(self, request) -> Response:
        """GET /reviews/bus_reviews/?bus_id=<uuid>"""
        bus_id = request.query_params.get('bus_id')
        if not bus_id:
            # Error Code: REV-VIEWS-VAL-001
            # Message: bus_id query parameter required
            # Cause: Missing bus_id in query parameters
            # Solution: Add ?bus_id=<uuid> to the request URL
            return Response(
                {'error': 'bus_id required', 'code': 'REV-VIEWS-VAL-001'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            uuid_mod.UUID(bus_id)
        except (ValueError, AttributeError):
            return Response(
                {'error': 'bus_id must be a valid UUID', 'code': 'REV-VIEWS-VAL-002'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = BusReview.objects.filter(
            bus_id=bus_id, is_approved=True,
        ).select_related('customer', 'bus', 'operator')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = BusReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(BusReviewSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def moderate(self, request, pk=None) -> Response:
        """Admin approves / flags / removes a review."""
        review = self.get_object()
        review = ReviewService.moderate_review(
            review=review,
            action=request.data.get('action', ''),
        )
        return Response(BusReviewSerializer(review).data)


# ═══════════════════════════════════════════════════════════════
#  OPERATOR REVIEW
# ═══════════════════════════════════════════════════════════════


class OperatorReviewViewSet(viewsets.ModelViewSet):
    """Operator review CRUD.

    Only users who have completed a booking with the operator
    can leave a review, preventing review spam.
    """

    serializer_class = OperatorReviewSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'operator_reviews'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self) -> QuerySet:
        """Admin sees all; public sees only approved reviews."""
        qs = OperatorReview.objects.select_related('reviewer', 'operator')
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return qs
        return qs.filter(is_approved=True)

    def perform_create(self, serializer) -> None:
        """Attach the reviewer and validate they have a completed booking with this operator."""
        operator = serializer.validated_data.get('operator')

        # Ensure reviewer has at least one completed booking with this operator
        from apps.bookings.models import Booking
        has_completed_booking = Booking.objects.filter(
            customer=self.request.user,
            operator=operator,
            status='completed',
        ).exists()

        if not has_completed_booking:
            from rest_framework.exceptions import ValidationError
            # Error Code: REV-VIEWS-VAL-003
            # Message: No completed booking with this operator
            # Cause: User has never completed a trip with this operator
            # Solution: Only review operators you have booked with
            raise ValidationError(
                'You can only review operators you have completed a booking with.',
                code='REV-VIEWS-VAL-003',
            )

        serializer.save(reviewer=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def operator_reviews(self, request) -> Response:
        """GET /operator-reviews/operator_reviews/?operator_id=<uuid>"""
        operator_id = request.query_params.get('operator_id')
        if not operator_id:
            # Error Code: REV-VIEWS-VAL-002
            # Message: operator_id query parameter required
            # Cause: Missing operator_id in query parameters
            # Solution: Add ?operator_id=<uuid> to the request URL
            return Response(
                {'error': 'operator_id required', 'code': 'REV-VIEWS-VAL-002'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            uuid_mod.UUID(operator_id)
        except (ValueError, AttributeError):
            return Response(
                {'error': 'operator_id must be a valid UUID', 'code': 'REV-VIEWS-VAL-002'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = OperatorReview.objects.filter(
            operator_id=operator_id, is_approved=True,
        ).select_related('reviewer', 'operator')
        # Paginate results to prevent OOM on large result sets
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                OperatorReviewSerializer(page, many=True).data,
            )
        return Response(OperatorReviewSerializer(qs, many=True).data)
