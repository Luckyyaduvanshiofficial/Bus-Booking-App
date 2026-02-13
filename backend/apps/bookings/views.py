"""Booking, Payment, and Coupon ViewSets – thin controllers.

All business logic is delegated to services.py.
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdmin, IsCustomer, IsOperatorOrAdmin

from .models import Booking, BookingHistory, Coupon, Payment
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingHistorySerializer,
    BookingListSerializer,
    BookingStatusUpdateSerializer,
    CouponApplySerializer,
    CouponSerializer,
    PaymentSerializer,
)
from .services import BookingService, CouponService, PaymentService


# ═══════════════════════════════════════════════════════════════
#  BOOKING
# ═══════════════════════════════════════════════════════════════


class BookingViewSet(viewsets.ModelViewSet):
    """Booking CRUD with status transitions.

    Delegates all business logic to BookingService.
    """

    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'trip_type']
    ordering_fields = ['pickup_date', 'created_at', 'total_amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingDetailSerializer

    def get_queryset(self) -> QuerySet:
        """Filter bookings by user role with optimized queries."""
        user = self.request.user
        qs = Booking.objects.select_related(
            'customer', 'operator', 'bus',
        ).prefetch_related('payments', 'history')

        if user.role == 'customer':
            return qs.filter(customer=user)
        if user.role == 'operator':
            return qs.filter(operator=user)
        return qs  # Admin

    def perform_create(self, serializer) -> None:
        """Delegate booking creation to BookingService."""
        # Error Code: BOK-VIEWS-PERM-001
        # Message: Only customers can create bookings
        # Cause: Non-customer tried to book
        # Solution: Check user.role == 'customer'
        if self.request.user.role != 'customer':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                'Only customers can create bookings.',
                code='BOK-VIEWS-PERM-001',
            )

        booking = BookingService.create_booking(
            customer=self.request.user,
            validated_data=serializer.validated_data,
        )
        serializer.instance = booking

    @action(detail=True, methods=['post'], permission_classes=[IsOperatorOrAdmin])
    def respond(self, request, pk=None) -> Response:
        """Operator confirms or rejects a pending booking.

        Accepts JSON body:
            {
                "status": "confirmed" | "rejected",
                "reason": "optional rejection reason"
            }

        Error Codes:
            BOK-VIEWS-PERM-002: Only operator can accept/reject bookings
            BOK-SERV-VAL-001: Booking is not in pending status
            BOK-SERV-VAL-002: Invalid respond status
        """
        booking = self.get_object()
        ser = BookingStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        booking = BookingService.respond_to_booking(
            booking=booking,
            new_status=ser.validated_data['status'],
            reason=ser.validated_data.get('reason', ''),
            responded_by=request.user,
        )
        return Response(BookingDetailSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None) -> Response:
        """Cancel a booking."""
        booking = self.get_object()

        if booking.customer != request.user and request.user.role != 'admin':
            # Error Code: BOK-VIEWS-PERM-003
            # Message: Not authorized to cancel this booking
            # Cause: User is not the booking customer or an admin
            # Solution: Only the booking owner or admin can cancel
            return Response(
                {'error': 'Not authorized', 'code': 'BOK-VIEWS-PERM-003'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Error Code: BOK-VIEWS-VAL-001
        # Message: Booking must be in pending status to cancel
        # Cause: Wrong status transition
        # Solution: Check booking.status
        if not booking.can_cancel():
            return Response(
                {'error': 'Booking cannot be cancelled in current status',
                 'code': 'BOK-VIEWS-VAL-001'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = BookingService.cancel_booking(
            booking=booking,
            reason=request.data.get('reason', 'Cancelled by customer'),
            cancelled_by=request.user,
        )
        return Response(BookingDetailSerializer(booking).data)

    @action(detail=True, methods=['post'], permission_classes=[IsOperatorOrAdmin])
    def complete(self, request, pk=None) -> Response:
        """Mark a confirmed booking as completed.

        Sets booking.status = 'completed' and booking.completed_at = now().
        Creates BookingHistory entry.
        Increments trip counters on Bus and User.

        Only operators or admins can mark bookings complete.
        Booking must be in 'confirmed' status.

        Error Codes:
            BOK-SERV-CONFLICT-003: Only confirmed bookings can be completed
        """
        booking = self.get_object()
        booking = BookingService.complete_booking(
            booking=booking,
            completed_by=request.user,
        )
        return Response(BookingDetailSerializer(booking).data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None) -> Response:
        """Get status change history for a booking."""
        booking = self.get_object()
        qs = BookingHistory.objects.filter(
            booking=booking,
        ).select_related('created_by').order_by('-created_at')
        return Response(BookingHistorySerializer(qs, many=True).data)


# ═══════════════════════════════════════════════════════════════
#  PAYMENT
# ═══════════════════════════════════════════════════════════════


class PaymentViewSet(viewsets.ModelViewSet):
    """Payment CRUD with initiate/confirm actions.

    Delegates business logic to PaymentService.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Filter payments by user role with optimized queries."""
        user = self.request.user
        qs = Payment.objects.select_related('booking', 'booking__customer')

        if user.role == 'customer':
            return qs.filter(booking__customer=user)
        if user.role == 'operator':
            return qs.filter(booking__operator=user)
        return qs

    @action(detail=False, methods=['post'])
    def initiate(self, request) -> Response:
        """Create a payment for a booking.

        Accepts JSON body:
            {
                "booking_id": "<uuid>",
                "payment_method": "upi" | "card" | "netbanking" | "wallet"
            }

        Retrieves booking by booking_id (NOT 'booking').
        Booking must belong to request.user and be in 'confirmed' status.

        Error Codes:
            BOK-VIEWS-NOTFOUND-001: Booking not found or not owned by user
            PAY-VIEWS-VAL-001: Booking must be confirmed before payment
            PAY-VIEWS-CONFLICT-001: Booking already fully paid
        """
        booking_id = request.data.get('booking_id')
        try:
            booking = Booking.objects.get(id=booking_id, customer=request.user)
        except Booking.DoesNotExist:
            # Error Code: BOK-VIEWS-NOTFOUND-001
            # Message: Booking not found
            # Cause: Invalid booking_id or booking not owned by user
            # Solution: Verify booking_id exists and belongs to the customer
            return Response(
                {'error': 'Booking not found', 'code': 'BOK-VIEWS-NOTFOUND-001'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Error Code: PAY-VIEWS-VAL-002
        # Message: Booking must be confirmed before payment
        # Cause: Booking status is not 'confirmed'
        # Solution: Wait for operator to confirm the booking first
        if booking.status != Booking.Status.CONFIRMED:
            return Response(
                {'error': 'Booking must be confirmed before payment',
                 'code': 'PAY-VIEWS-VAL-002'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Error Code: PAY-VIEWS-CONFLICT-001
        # Message: Booking already paid
        # Cause: Duplicate payment
        # Solution: Check booking.payment_status
        if booking.payment_status == 'fully_paid':
            return Response(
                {'error': 'Booking is already fully paid',
                 'code': 'PAY-VIEWS-CONFLICT-001'},
                status=status.HTTP_409_CONFLICT,
            )

        payment = PaymentService.initiate_payment(
            booking=booking,
            customer=request.user,
            payment_method=request.data.get('payment_method', 'upi'),
        )
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None) -> Response:
        """Confirm payment after Cashfree callback."""
        try:
            payment = self.get_object()
        except Exception:
            # Error Code: PAY-VIEWS-NOTFOUND-001
            # Message: Payment not found
            # Cause: Invalid payment_id
            # Solution: Check payment exists
            return Response(
                {'error': 'Payment not found', 'code': 'PAY-VIEWS-NOTFOUND-001'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.booking.customer != request.user and request.user.role != 'admin':
            # Error Code: PAY-VIEWS-PERM-001
            # Message: Not authorized to confirm this payment
            # Cause: User is not the booking owner or admin
            # Solution: Only the booking customer or admin can confirm payment
            return Response(
                {'error': 'Not authorized', 'code': 'PAY-VIEWS-PERM-001'},
                status=status.HTTP_403_FORBIDDEN,
            )

        payment = PaymentService.confirm_payment(
            payment=payment,
            cf_payment_id=request.data.get('cf_payment_id', ''),
            metadata=request.data.get('metadata', {}),
            confirmed_by=request.user,
        )
        return Response(PaymentSerializer(payment).data)


# ═══════════════════════════════════════════════════════════════
#  COUPON
# ═══════════════════════════════════════════════════════════════


class CouponViewSet(viewsets.ModelViewSet):
    """Coupon CRUD + apply action.

    Delegates validation logic to CouponService.
    """

    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.action in ('apply',):
            return [IsCustomer()]
        return [IsAdmin()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request) -> Response:
        """Validate and apply a coupon code."""
        ser = CouponApplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        result = CouponService.validate_and_calculate(
            code=ser.validated_data['code'],
            booking_amount=ser.validated_data['booking_amount'],
            user=request.user,
        )
        return Response({
            'coupon': CouponSerializer(result['coupon']).data,
            'discount': str(result['discount']),
            'final_amount': str(result['final_amount']),
        })
