from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone

from .models import Booking, Payment, BookingHistory, Coupon, CouponUsage
from .serializers import (
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer,
    BookingStatusUpdateSerializer, BookingHistorySerializer,
    PaymentSerializer, CouponSerializer, CouponApplySerializer,
)
from apps.users.permissions import IsCustomer, IsOperator, IsAdmin, IsOperatorOrAdmin


# ═══════════════════════════════════════════════════════════════
#  BOOKING
# ═══════════════════════════════════════════════════════════════

class BookingViewSet(viewsets.ModelViewSet):
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

    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Booking.objects.filter(customer=user)
        if user.role == 'operator':
            return Booking.objects.filter(operator=user)
        return Booking.objects.all()  # Admin

    # ── Create Booking ────────────────────────────────────────

    def perform_create(self, serializer):
        from apps.buses.models import Bus, AvailabilityBlock

        bus = serializer.validated_data['bus']
        pickup_date = serializer.validated_data['pickup_date']

        # Check availability
        if AvailabilityBlock.objects.filter(bus=bus, blocked_date=pickup_date).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Bus is not available on the selected date.')

        # Calculate pricing
        estimated_km = serializer.validated_data.get('estimated_km') or 0
        base_amount = bus.base_price or Decimal('0')
        distance_charge = Decimal(str(estimated_km)) * (bus.price_per_km or Decimal('0'))
        driver_charge = bus.driver_charge or Decimal('0')
        night_charge = bus.night_charge or Decimal('0')
        toll_estimate = Decimal('0')
        subtotal = base_amount + distance_charge + driver_charge + night_charge + toll_estimate

        platform_fee = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))

        # Commission (from operator's rate)
        commission_rate = bus.operator.commission_rate or Decimal('10')
        commission_amount = (subtotal * commission_rate / 100).quantize(Decimal('0.01'))
        operator_payout = subtotal - commission_amount

        total_amount = subtotal + platform_fee

        serializer.save(
            customer=self.request.user,
            operator=bus.operator,
            base_amount=base_amount + distance_charge,
            driver_charge=driver_charge,
            night_charge=night_charge,
            toll_estimate=toll_estimate,
            platform_fee=platform_fee,
            total_amount=total_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            operator_payout=operator_payout,
        )

        # Block date
        AvailabilityBlock.objects.create(
            bus=bus,
            blocked_date=pickup_date,
            block_reason='booked_platform',
            booking=serializer.instance,
        )

        # Create history entry
        BookingHistory.objects.create(
            booking=serializer.instance,
            old_status='',
            new_status='pending',
            reason='Booking created',
            created_by=self.request.user,
        )

    # ── Operator responds (confirm / reject) ─────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsOperatorOrAdmin])
    def respond(self, request, pk=None):
        """Operator confirms or rejects a pending booking."""
        booking = self.get_object()

        if booking.status != 'pending':
            return Response({'error': 'Booking is not pending'},
                            status=status.HTTP_400_BAD_REQUEST)

        ser = BookingStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_status = ser.validated_data['status']
        reason = ser.validated_data.get('reason', '')

        old_status = booking.status

        if new_status == 'confirmed':
            booking.status = 'confirmed'
            booking.operator_response = 'accepted'
            booking.operator_response_at = timezone.now()
        elif new_status == 'rejected':
            booking.status = 'cancelled_by_operator'
            booking.operator_response = 'rejected'
            booking.operator_response_at = timezone.now()
            booking.rejection_reason = reason
            # Unblock date
            from apps.buses.models import AvailabilityBlock
            AvailabilityBlock.objects.filter(booking=booking).delete()
        else:
            return Response({'error': 'Invalid status for respond'},
                            status=status.HTTP_400_BAD_REQUEST)

        booking.save()

        BookingHistory.objects.create(
            booking=booking, old_status=old_status,
            new_status=booking.status, reason=reason,
            created_by=request.user,
        )
        return Response(BookingDetailSerializer(booking).data)

    # ── Cancel ────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()

        # Auth check
        if booking.customer != request.user and request.user.role != 'admin':
            return Response({'error': 'Not authorized'},
                            status=status.HTTP_403_FORBIDDEN)

        if booking.status in ('completed', 'cancelled_by_customer', 'cancelled_by_operator'):
            return Response({'error': 'Cannot cancel this booking'},
                            status=status.HTTP_400_BAD_REQUEST)

        old_status = booking.status
        booking.status = 'cancelled_by_customer'
        booking.cancellation_reason = request.data.get('reason', 'Cancelled by customer')
        booking.cancelled_at = timezone.now()
        booking.save()

        # Unblock date
        from apps.buses.models import AvailabilityBlock
        AvailabilityBlock.objects.filter(booking=booking).delete()

        BookingHistory.objects.create(
            booking=booking, old_status=old_status,
            new_status='cancelled_by_customer', reason=booking.cancellation_reason,
            created_by=request.user,
        )
        return Response(BookingDetailSerializer(booking).data)

    # ── Complete ──────────────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsOperatorOrAdmin])
    def complete(self, request, pk=None):
        booking = self.get_object()
        if booking.status != 'confirmed':
            return Response({'error': 'Only confirmed bookings can be completed'},
                            status=status.HTTP_400_BAD_REQUEST)

        old_status = booking.status
        booking.status = 'completed'
        booking.completed_at = timezone.now()
        booking.save()

        # Increment counters
        booking.customer.total_bookings += 1
        booking.customer.save(update_fields=['total_bookings'])
        booking.bus.total_trips += 1
        booking.bus.save(update_fields=['total_trips'])
        booking.operator.total_bookings += 1
        booking.operator.save(update_fields=['total_bookings'])

        BookingHistory.objects.create(
            booking=booking, old_status=old_status,
            new_status='completed', reason='Trip completed',
            created_by=request.user,
        )
        return Response(BookingDetailSerializer(booking).data)

    # ── History ───────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        booking = self.get_object()
        qs = BookingHistory.objects.filter(booking=booking).order_by('-created_at')
        return Response(BookingHistorySerializer(qs, many=True).data)


# ═══════════════════════════════════════════════════════════════
#  PAYMENT
# ═══════════════════════════════════════════════════════════════

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Payment.objects.filter(booking__customer=user)
        if user.role == 'operator':
            return Payment.objects.filter(booking__operator=user)
        return Payment.objects.all()

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Create a Cashfree order for a booking."""
        booking_id = request.data.get('booking_id')
        try:
            booking = Booking.objects.get(id=booking_id, customer=request.user)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'},
                            status=status.HTTP_404_NOT_FOUND)

        amount = booking.total_amount
        if booking.payment_mode == 'online_advance':
            amount = booking.advance_amount or (booking.total_amount * Decimal('0.3')).quantize(Decimal('0.01'))

        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_type='advance' if booking.payment_mode == 'online_advance' else 'full',
            payment_method=request.data.get('payment_method', 'upi'),
        )

        # TODO: Create Cashfree order via SDK and populate cf_order_id
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm payment after Cashfree callback."""
        payment = self.get_object()

        if payment.booking.customer != request.user and request.user.role != 'admin':
            return Response({'error': 'Not authorized'},
                            status=status.HTTP_403_FORBIDDEN)

        payment.status = 'captured'
        payment.cf_payment_id = request.data.get('cf_payment_id', '')
        payment.metadata = request.data.get('metadata', {})
        payment.save()

        booking = payment.booking
        booking.payment_status = 'fully_paid'
        if booking.status == 'pending':
            booking.status = 'confirmed'
        booking.save()

        BookingHistory.objects.create(
            booking=booking, old_status='pending',
            new_status=booking.status, reason='Payment confirmed',
            created_by=request.user,
        )
        return Response(PaymentSerializer(payment).data)


# ═══════════════════════════════════════════════════════════════
#  COUPON
# ═══════════════════════════════════════════════════════════════

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.action in ('apply',):
            return [IsCustomer()]
        return [IsAdmin()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request):
        """Validate and apply a coupon code."""
        ser = CouponApplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        code = ser.validated_data['code']
        amount = ser.validated_data['booking_amount']

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon code'},
                            status=status.HTTP_404_NOT_FOUND)

        if not coupon.is_valid:
            return Response({'error': 'Coupon is expired or exhausted'},
                            status=status.HTTP_400_BAD_REQUEST)

        if coupon.min_booking and amount < coupon.min_booking:
            return Response(
                {'error': f'Minimum booking amount is ₹{coupon.min_booking}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Per-user limit
        user_uses = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
        if coupon.per_user_limit and user_uses >= coupon.per_user_limit:
            return Response({'error': 'You have already used this coupon'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount = (amount * coupon.discount_value / 100).quantize(Decimal('0.01'))
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            discount = coupon.discount_value

        return Response({
            'coupon': CouponSerializer(coupon).data,
            'discount': str(discount),
            'final_amount': str(amount - discount),
        })
