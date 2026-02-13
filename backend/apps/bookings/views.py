"""Booking, Payment, and Coupon ViewSets – thin controllers.

All business logic is delegated to services.py.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import QuerySet
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

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
    PaymentInitiateSerializer,
    PaymentSerializer,
)
from .services import BookingService, CouponService, PaymentService

logger = logging.getLogger(__name__)


class BookingCreateThrottle(UserRateThrottle):
    """Limit booking creation to 5 per minute per user.

    Prevents spam-booking that would lock up bus availability
    with dozens of pending bookings.
    """
    rate = '5/minute'


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

    def get_throttles(self):
        """Apply stricter throttle on booking creation to prevent spam."""
        if self.action == 'create':
            return [BookingCreateThrottle()]
        return super().get_throttles()

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
        ).prefetch_related('payments', 'history', 'bus__photos')

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

        # Ownership check: operator can only respond to their own bookings
        if (request.user.role == 'operator'
                and booking.operator != request.user):
            # Error Code: BOK-VIEWS-PERM-004
            # Message: Not authorized to respond to this booking
            # Cause: Operator tried to respond to another operator's booking
            # Solution: Only the booking's operator or an admin can respond
            return Response(
                {'error': 'Not authorized to respond to this booking',
                 'code': 'BOK-VIEWS-PERM-004'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = BookingStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        booking = BookingService.respond_to_booking(
            booking=booking,
            new_status=ser.validated_data['status'],
            reason=ser.validated_data.get('reason', ''),
            responded_by=request.user,
        )
        return Response(
            BookingDetailSerializer(booking, context={'request': request}).data,
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None) -> Response:
        """Cancel a booking.

        Customers can cancel their own bookings.
        Operators can cancel bookings assigned to them.
        Admins can cancel any booking.

        Error Codes:
            BOK-VIEWS-PERM-003: Not authorized to cancel
            BOK-VIEWS-VAL-001: Booking cannot be cancelled in current status
        """
        booking = self.get_object()

        # Authorization: customer owns it, operator owns it, or admin
        is_customer = booking.customer == request.user
        is_operator = (request.user.role == 'operator'
                       and booking.operator == request.user)
        is_admin = request.user.role == 'admin'

        if not (is_customer or is_operator or is_admin):
            # Error Code: BOK-VIEWS-PERM-003
            # Message: Not authorized to cancel this booking
            # Cause: User is not the booking customer, operator, or an admin
            # Solution: Only the booking parties or admin can cancel
            return Response(
                {'error': 'Not authorized', 'code': 'BOK-VIEWS-PERM-003'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Error Code: BOK-VIEWS-VAL-001
        # Message: Booking must be in cancellable status
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
        return Response(
            BookingDetailSerializer(booking, context={'request': request}).data,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsOperatorOrAdmin])
    def complete(self, request, pk=None) -> Response:
        """Mark a confirmed booking as completed.

        Sets booking.status = 'completed' and booking.completed_at = now().
        Creates BookingHistory entry.
        Increments trip counters on Bus and User.

        Only the booking's operator or an admin can mark bookings complete.
        Booking must be in 'confirmed' status.

        Error Codes:
            BOK-VIEWS-PERM-005: Not authorized to complete this booking
            BOK-SERV-CONFLICT-003: Only confirmed bookings can be completed
        """
        booking = self.get_object()

        # Ownership check: operator can only complete their own bookings
        if (request.user.role == 'operator'
                and booking.operator != request.user):
            # Error Code: BOK-VIEWS-PERM-005
            # Message: Not authorized to complete this booking
            # Cause: Operator tried to complete another operator's booking
            # Solution: Only the booking's operator or an admin can complete
            return Response(
                {'error': 'Not authorized to complete this booking',
                 'code': 'BOK-VIEWS-PERM-005'},
                status=status.HTTP_403_FORBIDDEN,
            )

        booking = BookingService.complete_booking(
            booking=booking,
            completed_by=request.user,
        )
        return Response(
            BookingDetailSerializer(booking, context={'request': request}).data,
        )

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


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Payment read-only endpoints with initiate/confirm actions.

    Uses GenericViewSet + read-only mixins to prevent direct
    create/update/delete on financial records. Payment creation
    only through the initiate action; confirmation only through
    the confirm action or Cashfree webhook.

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
        input_serializer = PaymentInitiateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        booking_id = input_serializer.validated_data['booking_id']
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
            payment_method=input_serializer.validated_data['payment_method'],
        )
        return Response(
            PaymentSerializer(payment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def confirm(self, request, pk=None) -> Response:
        """Confirm payment manually (admin-only).

        For Cashfree production webhooks, use /api/v1/bookings/payments/webhook/
        instead. This endpoint exists ONLY for admin-initiated manual
        confirmations (e.g., cash payments, support overrides).

        Restricted to admin to prevent customers from self-confirming
        payments they never made through Cashfree.

        Error Codes:
            PAY-VIEWS-NOTFOUND-001: Payment not found
            PAY-VIEWS-PERM-001: Only admins can confirm payments
        """
        try:
            payment = self.get_object()
        except Http404:
            # Error Code: PAY-VIEWS-NOTFOUND-001
            # Message: Payment not found
            # Cause: Invalid payment_id
            # Solution: Check payment exists
            return Response(
                {'error': 'Payment not found', 'code': 'PAY-VIEWS-NOTFOUND-001'},
                status=status.HTTP_404_NOT_FOUND,
            )

        actual_amount = None
        if 'amount' in request.data:
            try:
                actual_amount = Decimal(str(request.data['amount']))
            except (InvalidOperation, TypeError, ValueError):
                return Response(
                    {'error': 'Invalid amount', 'code': 'PAY-VIEWS-VAL-004'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        payment = PaymentService.confirm_payment(
            payment=payment,
            cf_payment_id=request.data.get('cf_payment_id', ''),
            actual_amount=actual_amount,
            metadata=request.data.get('metadata', {}),
            confirmed_by=request.user,
        )
        return Response(PaymentSerializer(payment, context={'request': request}).data)


# ═══════════════════════════════════════════════════════════════
#  CASHFREE WEBHOOK
# ═══════════════════════════════════════════════════════════════


def _verify_cashfree_signature(payload_bytes: bytes, signature: str) -> bool:
    """Verify Cashfree webhook HMAC-SHA256 signature.

    Cashfree sends a base64-encoded HMAC-SHA256 signature in the
    'x-webhook-signature' header. We compute the same and compare
    using hmac.compare_digest to prevent timing attacks.

    Args:
        payload_bytes: Raw request body bytes.
        signature: Base64-encoded signature from the webhook header.

    Returns:
        True if signature is valid, False otherwise.
    """
    secret = getattr(settings, 'CASHFREE_SECRET_KEY', '')
    if not secret:
        logger.error('CASHFREE_SECRET_KEY not configured [PAY-WEBHOOK-CONFIG-001]')
        return False

    # Cashfree uses base64-encoded HMAC-SHA256, not hex digest
    computed = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(computed).decode('utf-8')
    return hmac.compare_digest(expected, signature)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def cashfree_webhook(request) -> Response:
    """Handle Cashfree payment webhook notifications.

    Verifies HMAC-SHA256 signature before processing. This endpoint is
    unauthenticated (AllowAny) since Cashfree servers call it directly.
    Explicitly @csrf_exempt to ensure Django's CSRF middleware never
    blocks incoming Cashfree webhook POSTs.

    Cashfree payload includes:
        - data.order.order_id → maps to our Payment.id
        - data.payment.cf_payment_id → Cashfree payment ID
        - data.payment.payment_amount → actual paid amount
        - type → event type (e.g. 'PAYMENT_SUCCESS_WEBHOOK')

    Error Codes:
        PAY-WEBHOOK-PERM-001: Invalid webhook signature
        PAY-WEBHOOK-NOTFOUND-001: Payment not found for order_id
    """
    # Step 1: Verify webhook signature to ensure request is from Cashfree
    signature = request.headers.get('x-webhook-signature', '')
    if not _verify_cashfree_signature(request.body, signature):
        # Error Code: PAY-WEBHOOK-PERM-001
        # Message: Invalid webhook signature
        # Cause: Request not from Cashfree or secret key mismatch
        # Solution: Verify CASHFREE_SECRET_KEY matches Cashfree dashboard
        logger.warning('Invalid Cashfree webhook signature [PAY-WEBHOOK-PERM-001]')
        return Response(
            {'error': 'Invalid signature', 'code': 'PAY-WEBHOOK-PERM-001'},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Step 2: Parse payload
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return Response(
            {'error': 'Invalid JSON'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    event_type = payload.get('type', '')
    data = payload.get('data', {})
    order_data = data.get('order', {})
    payment_data = data.get('payment', {})

    order_id = order_data.get('order_id', '')
    cf_payment_id = payment_data.get('cf_payment_id', '')
    payment_amount = payment_data.get('payment_amount')

    # Step 3: Only process payment success events
    if event_type != 'PAYMENT_SUCCESS_WEBHOOK':
        return Response({'status': 'ignored'})

    # Step 4: Look up payment
    try:
        payment = Payment.objects.select_related('booking').get(id=order_id)
    except (Payment.DoesNotExist, ValueError):
        # Error Code: PAY-WEBHOOK-NOTFOUND-001
        # Message: Payment not found
        # Cause: order_id from webhook doesn't match any Payment
        # Solution: Check Cashfree dashboard for correct order_id
        logger.warning(
            'Webhook payment not found: order_id=%s [PAY-WEBHOOK-NOTFOUND-001]',
            order_id,
        )
        return Response(
            {'error': 'Payment not found', 'code': 'PAY-WEBHOOK-NOTFOUND-001'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Step 5: Confirm payment with amount verification
    try:
        actual_amount = Decimal(str(payment_amount)) if payment_amount is not None else None
    except (InvalidOperation, TypeError, ValueError):
        return Response(
            {'error': 'Invalid payment amount', 'code': 'PAY-WEBHOOK-VAL-001'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        PaymentService.confirm_payment(
            payment=payment,
            cf_payment_id=cf_payment_id,
            actual_amount=actual_amount,
            metadata=data,
        )
    except ValidationError as e:
        # Amount mismatch or business validation — payment is already marked failed
        # in the service layer. Return 200 to acknowledge the webhook and prevent
        # Cashfree from retrying indefinitely on a legitimate fraud detection.
        logger.warning(
            'Webhook validation error for order %s: %s [PAY-SERV-VAL-001]',
            order_id,
            e,
        )
        return Response({'status': 'failed', 'reason': str(e)})
    except Exception:
        logger.exception('Webhook payment confirmation failed for order %s', order_id)
        return Response(
            {'error': 'Processing failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({'status': 'ok'})


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

    @action(detail=False, methods=['post'], permission_classes=[IsCustomer])
    def apply(self, request) -> Response:
        """Validate and apply a coupon code.

        Only customers can apply coupons. The booking_amount must
        be provided to calculate the discount, but when the coupon
        is actually applied during booking creation, the server-side
        pricing is used.

        Error Codes:
            BOK-SERV-VAL-003: Invalid coupon code
            BOK-SERV-VAL-004: Coupon expired or exhausted
            BOK-SERV-VAL-005: Booking amount below minimum
            BOK-SERV-VAL-006: Per-user limit reached
        """
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
