"""User ViewSets & auth FBVs – thin controllers.

All business logic is delegated to services.py.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes as perm_classes, throttle_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import CustomUser, Document, Notification
from .permissions import IsAdmin, IsOperator, IsOperatorOrAdmin
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentVerifySerializer,
    NotificationSerializer,
    OperatorPublicSerializer,
    OperatorRegistrationSerializer,
    OperatorSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from .services import AuthService, DocumentService, OperatorService, UserService


class OTPThrottle(ScopedRateThrottle):
    """Rate limiter for OTP endpoints — prevents SMS abuse."""
    scope = 'otp'


# ═══════════════════════════════════════════════════════════════
#  AUTH  –  Supabase OTP flow
# ═══════════════════════════════════════════════════════════════


@api_view(['POST'])
@perm_classes([AllowAny])
@throttle_classes([OTPThrottle])
def send_otp(request) -> Response:
    """Send OTP to phone number via Supabase Auth."""
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    result = AuthService.send_otp(phone=serializer.validated_data['phone'])
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@perm_classes([AllowAny])
@throttle_classes([OTPThrottle])
def verify_otp(request) -> Response:
    """Verify OTP and return auth token."""
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    result = AuthService.verify_otp(
        phone=serializer.validated_data['phone'],
        otp=serializer.validated_data['otp'],
    )
    return Response(result)


@api_view(['POST'])
@perm_classes([IsAuthenticated])
def register(request) -> Response:
    """Complete user registration (requires auth token from verify_otp).

    This endpoint requires the DRF token returned by verify_otp, ensuring
    the user has actually completed OTP verification before they can set
    their profile fields (name, email, role). Without this guard, anyone
    could call register directly with any phone number and create/update
    user records without proving phone ownership.

    Error Codes:
        USR-VIEWS-AUTH-001: Authentication required (no token)
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Only allow the authenticated user to register their own phone
    if serializer.validated_data['phone'] != request.user.phone:
        # Error Code: USR-VIEWS-PERM-003
        # Message: Phone mismatch — can only register your own number
        # Cause: Token belongs to a different phone number
        # Solution: Use the token from verify_otp for the same phone
        return Response(
            {'error': 'Phone number does not match authenticated user',
             'code': 'USR-VIEWS-PERM-003'},
            status=status.HTTP_403_FORBIDDEN,
        )

    result = AuthService.register_user(validated_data=serializer.validated_data)
    http_status = (
        status.HTTP_201_CREATED if result.get('created') else status.HTTP_200_OK
    )
    result.pop('created', None)
    return Response(result, status=http_status)


# ═══════════════════════════════════════════════════════════════
#  USER PROFILE
# ═══════════════════════════════════════════════════════════════


class UserViewSet(viewsets.ModelViewSet):
    """Admin-level user management + self-service profile endpoints."""

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # Admin-only for list, retrieve, update, partial_update, destroy.
        # Any authenticated user modifying a user record (except via /me/) must be admin.
        if self.action in ('list', 'retrieve', 'destroy', 'update', 'partial_update'):
            return [IsAdmin()]
        return [IsAuthenticated()]

    # ── Self-service ──────────────────────────────────────────

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request) -> Response:
        """Return current user's full profile."""
        return Response(UserProfileSerializer(request.user).data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request) -> Response:
        """Update current user's profile."""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── Admin actions ─────────────────────────────────────────

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def verify(self, request, pk=None) -> Response:
        """Admin approves / rejects an operator."""
        try:
            user = self.get_object()
        except Exception:
            # Error Code: USR-VIEWS-NOTFOUND-001
            # Message: User not found
            # Cause: User ID doesn't exist
            # Solution: Check user_id in request
            return Response(
                {'error': 'User not found', 'code': 'USR-VIEWS-NOTFOUND-001'},
                status=status.HTTP_404_NOT_FOUND,
            )
        user = UserService.verify_user(
            user=user,
            action=request.data.get('action', ''),
            reason=request.data.get('reason', ''),
        )
        return Response(UserSerializer(user).data)


# ═══════════════════════════════════════════════════════════════
#  OPERATOR
# ═══════════════════════════════════════════════════════════════


class OperatorViewSet(viewsets.ModelViewSet):
    """Operator management + dashboard."""

    queryset = CustomUser.objects.filter(role='operator')

    def get_serializer_class(self):
        """Use public serializer for list/retrieve — hide financial data from non-admins."""
        if self.action in ('list', 'retrieve'):
            if not self.request.user.is_authenticated or self.request.user.role not in ('admin', 'operator'):
                return OperatorPublicSerializer
            # Operators can see their own full profile via my_profile
            if self.request.user.role == 'operator' and self.action == 'retrieve':
                return OperatorPublicSerializer
        return OperatorSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated()]
        if self.action in ('register_as_operator', 'my_profile'):
            return [IsAuthenticated()]
        return [IsOperatorOrAdmin()]

    def get_queryset(self) -> QuerySet:
        """Optimized query with prefetch to avoid N+1 on documents."""
        return CustomUser.objects.filter(
            role='operator',
        ).prefetch_related('documents')

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register_as_operator(self, request) -> Response:
        """Convert current user to operator role."""
        serializer = OperatorRegistrationSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = OperatorService.register_as_operator(
            user=request.user,
            validated_data=serializer.validated_data,
        )
        return Response(OperatorSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsOperator])
    def my_profile(self, request) -> Response:
        """Return operator's own profile."""
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['get'], permission_classes=[IsOperator])
    def dashboard(self, request) -> Response:
        """Operator dashboard summary."""
        data = OperatorService.get_dashboard(operator=request.user)
        return Response(data)


# ═══════════════════════════════════════════════════════════════
#  DOCUMENT
# ═══════════════════════════════════════════════════════════════


class DocumentViewSet(viewsets.ModelViewSet):
    """Document upload and admin verification."""

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Admin sees all; others see only their own documents."""
        if self.request.user.role == 'admin':
            return Document.objects.select_related('user', 'verified_by').all()
        return Document.objects.filter(
            user=self.request.user,
        ).select_related('user', 'verified_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    def perform_create(self, serializer) -> None:
        """Attach authenticated user to the document.

        Validates that operator uploads their own documents.
        """
        if self.request.user.role not in ('operator', 'admin'):
            raise PermissionDenied(
                'Only operators can upload documents.',
                code='DOC-VIEWS-PERM-001',
            )

        # Error Code: DOC-VIEWS-PERM-001
        # Message: Only bus operator can upload documents
        # Cause: Unauthorized upload
        # Solution: Check bus ownership
        bus = serializer.validated_data.get('bus')
        if bus and bus.operator != self.request.user and self.request.user.role != 'admin':
            raise PermissionDenied(
                'You can only upload documents for your own buses.',
                code='DOC-VIEWS-PERM-001',
            )
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def verify(self, request, pk=None) -> Response:
        """Admin approves / rejects a document."""
        ser = DocumentVerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        doc = self.get_object()
        doc = DocumentService.verify_document(
            document=doc,
            action=ser.validated_data['action'],
            verified_by=request.user,
            rejection_reason=ser.validated_data.get('rejection_reason', ''),
        )
        return Response(DocumentSerializer(doc).data)


# ═══════════════════════════════════════════════════════════════
#  NOTIFICATION
# ═══════════════════════════════════════════════════════════════


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """User notifications – read-only with mark-read actions."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """Return only the authenticated user's notifications."""
        return Notification.objects.filter(
            user=self.request.user,
        ).select_related('user')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None) -> Response:
        """Mark a single notification as read."""
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({'status': 'read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request) -> Response:
        """Mark all unread notifications as read."""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all read'})
