"""User ViewSets & auth FBVs – thin controllers.

All business logic is delegated to services.py.
"""

from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes as perm_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser, Document, Notification
from .permissions import IsAdmin, IsOperator, IsOperatorOrAdmin
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentVerifySerializer,
    NotificationSerializer,
    OperatorRegistrationSerializer,
    OperatorSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from .services import AuthService, DocumentService, OperatorService, UserService


# ═══════════════════════════════════════════════════════════════
#  AUTH  –  Supabase OTP flow
# ═══════════════════════════════════════════════════════════════


@api_view(['POST'])
@perm_classes([AllowAny])
def send_otp(request) -> Response:
    """Send OTP to phone number via Supabase Auth."""
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    result = AuthService.send_otp(phone=serializer.validated_data['phone'])
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@perm_classes([AllowAny])
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
@perm_classes([AllowAny])
def register(request) -> Response:
    """Register a new user (after OTP verification)."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

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
        if self.action in ('list', 'retrieve', 'destroy'):
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
    serializer_class = OperatorSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated()]
        if self.action in ('register_as_operator', 'my_profile'):
            return [IsAuthenticated()]
        return [IsOperatorOrAdmin()]

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
        # Error Code: DOC-VIEWS-PERM-001
        # Message: Only bus operator can upload documents
        # Cause: Unauthorized upload
        # Solution: Check bus ownership
        bus = serializer.validated_data.get('bus')
        if bus and bus.operator != self.request.user and self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
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
