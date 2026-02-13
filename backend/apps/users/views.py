from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes as perm_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import CustomUser, Document, Notification
from .serializers import (
    UserSerializer, UserProfileSerializer,
    OperatorSerializer, OperatorRegistrationSerializer,
    DocumentSerializer, DocumentUploadSerializer, DocumentVerifySerializer,
    NotificationSerializer,
    OTPRequestSerializer, OTPVerifySerializer, RegisterSerializer,
)
from .permissions import IsAdmin, IsOperator, IsOperatorOrAdmin, IsOwnerOrAdmin


# ═══════════════════════════════════════════════════════════════
#  AUTH  –  Supabase OTP flow
# ═══════════════════════════════════════════════════════════════

@api_view(['POST'])
@perm_classes([AllowAny])
def send_otp(request):
    """Send OTP to phone number via Supabase Auth."""
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone']

    try:
        from django.conf import settings
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        supabase.auth.sign_in_with_otp({'phone': phone})
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Failed to send OTP: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@perm_classes([AllowAny])
def verify_otp(request):
    """Verify OTP and return auth token."""
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone']
    otp = serializer.validated_data['otp']

    try:
        from django.conf import settings
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        resp = supabase.auth.verify_otp({'phone': phone, 'token': otp, 'type': 'sms'})

        if not resp.user:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get or create Django user
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={
                'username': phone,
                'supabase_uid': resp.user.id,
            },
        )
        if not created and not user.supabase_uid:
            user.supabase_uid = resp.user.id
            user.save(update_fields=['supabase_uid'])

        # Issue DRF Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'is_new_user': created,
        })

    except Exception as e:
        return Response(
            {'error': f'Verification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@perm_classes([AllowAny])
def register(request):
    """Register a new user (after OTP verification)."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data['phone']
    user, created = CustomUser.objects.get_or_create(
        phone=phone,
        defaults={
            'username': phone,
            'name': serializer.validated_data.get('name', ''),
            'email': serializer.validated_data.get('email', ''),
            'role': serializer.validated_data.get('role', 'customer'),
        },
    )

    if not created:
        # Update fields for existing user
        for field in ('name', 'email', 'role'):
            val = serializer.validated_data.get(field)
            if val:
                setattr(user, field, val)
        user.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════
#  USER PROFILE
# ═══════════════════════════════════════════════════════════════

class UserViewSet(viewsets.ModelViewSet):
    """Admin-level user management + self-service profile endpoints."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'destroy'):
            return [IsAdmin()]
        return [IsAuthenticated()]

    # ── Self-service ──────────────────────────────────────────

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Return current user's full profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current user's profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── Admin actions ─────────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def verify(self, request, pk=None):
        """Admin approves / rejects an operator."""
        user = self.get_object()
        act = request.data.get('action')  # 'approve' | 'reject'

        if act == 'approve':
            user.is_verified = True
            user.verification_status = 'verified'
            user.save(update_fields=['is_verified', 'verification_status'])
        elif act == 'reject':
            user.verification_status = 'rejected'
            user.rejection_reason = request.data.get('reason', '')
            user.save(update_fields=['verification_status', 'rejection_reason'])
        else:
            return Response({'error': 'action must be approve or reject'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(UserSerializer(user).data)


# ═══════════════════════════════════════════════════════════════
#  OPERATOR
# ═══════════════════════════════════════════════════════════════

class OperatorViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.filter(role='operator')
    serializer_class = OperatorSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated()]
        if self.action in ('register_as_operator', 'my_profile'):
            return [IsAuthenticated()]
        return [IsOperatorOrAdmin()]

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register_as_operator(self, request):
        """Convert current user to operator role."""
        user = request.user
        if user.role == 'operator':
            return Response({'error': 'Already an operator'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = OperatorRegistrationSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user.role = 'operator'
        user.verification_status = 'pending'
        serializer.save()

        return Response(OperatorSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsOperator])
    def my_profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsOperator])
    def dashboard(self, request):
        """Operator dashboard summary."""
        from apps.bookings.models import Booking

        user = request.user
        bookings = Booking.objects.filter(operator=user)
        return Response({
            'total_buses': user.total_buses,
            'total_bookings': user.total_bookings,
            'rating_avg': float(user.rating_avg),
            'pending_bookings': bookings.filter(status='pending').count(),
            'active_bookings': bookings.filter(status='confirmed').count(),
            'completed_bookings': bookings.filter(status='completed').count(),
        })


# ═══════════════════════════════════════════════════════════════
#  DOCUMENT
# ═══════════════════════════════════════════════════════════════

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Document.objects.all()
        return Document.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def verify(self, request, pk=None):
        """Admin approves / rejects a document."""
        doc = self.get_object()
        ser = DocumentVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        act = ser.validated_data['action']
        if act == 'approve':
            doc.verification_status = 'verified'
            doc.verified_by = request.user
            from django.utils import timezone
            doc.verified_at = timezone.now()
        elif act == 'reject':
            doc.verification_status = 'rejected'
            doc.rejection_reason = ser.validated_data.get('rejection_reason', '')
            doc.verified_by = request.user
            from django.utils import timezone
            doc.verified_at = timezone.now()

        doc.save()
        return Response(DocumentSerializer(doc).data)


# ═══════════════════════════════════════════════════════════════
#  NOTIFICATION
# ═══════════════════════════════════════════════════════════════

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'status': 'read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all read'})
