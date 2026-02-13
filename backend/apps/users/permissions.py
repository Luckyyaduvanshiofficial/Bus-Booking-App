from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Allow access only to customers."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'customer'
        )


class IsOperator(BasePermission):
    """Allow access only to operators."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'operator'
        )


class IsAdmin(BasePermission):
    """Allow access only to admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission:
    - Admins can access anything.
    - Users can only access their own objects.
    Expects the object to have a `user`, `customer`, or `operator` FK pointing
    to the authenticated user.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        # Check common FK names
        for attr in ('user', 'customer', 'operator', 'reviewer', 'owner'):
            owner = getattr(obj, attr, None)
            if owner is not None:
                return owner == request.user
        return False


class IsOperatorOrAdmin(BasePermission):
    """Allow access to operators or admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('operator', 'admin')
        )


class IsAuthenticated(BasePermission):
    """Simple authenticated check (any role)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
