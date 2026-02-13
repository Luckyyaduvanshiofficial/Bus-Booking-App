from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import BusReview, OperatorReview
from .serializers import (
    BusReviewSerializer, BusReviewCreateSerializer,
    OperatorReviewSerializer,
)
from apps.users.permissions import IsCustomer, IsAdmin


# ═══════════════════════════════════════════════════════════════
#  BUS REVIEW
# ═══════════════════════════════════════════════════════════════

class BusReviewViewSet(viewsets.ModelViewSet):
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

    def get_queryset(self):
        # Admin sees all; public sees only approved
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return BusReview.objects.all()
        return BusReview.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        booking = serializer.validated_data['booking']
        serializer.save(
            customer=self.request.user,
            bus=booking.bus,
            operator=booking.operator,
        )

    # ── Reviews for a specific bus ────────────────────────────

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def bus_reviews(self, request):
        """GET /reviews/bus_reviews/?bus_id=<uuid>"""
        bus_id = request.query_params.get('bus_id')
        if not bus_id:
            return Response({'error': 'bus_id required'},
                            status=status.HTTP_400_BAD_REQUEST)

        qs = BusReview.objects.filter(bus_id=bus_id, is_approved=True)
        return Response(BusReviewSerializer(qs, many=True).data)

    # ── Admin moderation ─────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def moderate(self, request, pk=None):
        """Approve / flag a review."""
        review = self.get_object()
        act = request.data.get('action')  # 'approve' | 'flag' | 'remove'

        if act == 'approve':
            review.is_approved = True
            review.is_flagged = False
        elif act == 'flag':
            review.is_flagged = True
        elif act == 'remove':
            review.is_approved = False
        else:
            return Response({'error': 'action must be approve, flag, or remove'},
                            status=status.HTTP_400_BAD_REQUEST)
        review.save()
        return Response(BusReviewSerializer(review).data)


# ═══════════════════════════════════════════════════════════════
#  OPERATOR REVIEW
# ═══════════════════════════════════════════════════════════════

class OperatorReviewViewSet(viewsets.ModelViewSet):
    serializer_class = OperatorReviewSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'operator_reviews'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return OperatorReview.objects.all()
        return OperatorReview.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def operator_reviews(self, request):
        """GET /operator-reviews/operator_reviews/?operator_id=<uuid>"""
        operator_id = request.query_params.get('operator_id')
        if not operator_id:
            return Response({'error': 'operator_id required'},
                            status=status.HTTP_400_BAD_REQUEST)

        qs = OperatorReview.objects.filter(operator_id=operator_id, is_approved=True)
        return Response(OperatorReviewSerializer(qs, many=True).data)
