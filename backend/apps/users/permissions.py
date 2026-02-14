"""Custom DRF permission classes.

Uses TextChoices constants from CustomUser.Role for role checks.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from .models import CustomUser


class IsCustomer(BasePermission):
    """Allow access only to customers."""

    message = 'Only customers can access this endpoint. [USR-VIEWS-PERM-001]'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == CustomUser.Role.CUSTOMER
        )


class IsOperator(BasePermission):
    """Allow access only to verified operators.

    Unverified operators (verification_status != 'approved') are blocked
    from operator-only endpoints like creating buses and viewing dashboard.
    They must complete verification via the admin before accessing these.
    """

    message = 'Only verified operators can access this endpoint. [USR-VIEWS-PERM-003]'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == CustomUser.Role.OPERATOR
            and request.user.is_verified
        )


class IsAdmin(BasePermission):
    """Allow access only to admins."""

    message = 'Only admins can access this endpoint. [USR-VIEWS-PERM-002]'

    def has_permission(self, request, view) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == CustomUser.Role.ADMIN
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission.

    Admins can access anything.
    Users can only access their own objects (via user/customer/operator FK).
    """

    message = 'You do not have permission to access this object. [USR-VIEWS-PERM-003]'

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.role == CustomUser.Role.ADMIN:
            return True
        for attr in ('user', 'customer', 'operator', 'reviewer', 'owner'):
            owner = getattr(obj, attr, None)
            if owner is not None:
                return owner == request.user
        return False


class IsOperatorOrAdmin(BasePermission):
    """Allow access to operators or admins."""

    message = 'Only verified operators or admins can access this endpoint. [USR-VIEWS-PERM-004]'

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == CustomUser.Role.ADMIN:
            return True
        return (
            user.role == CustomUser.Role.OPERATOR
            and user.is_verified
        )
