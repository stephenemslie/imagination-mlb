from rest_framework.permissions import BasePermission, SAFE_METHODS, is_authenticated


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or
            request.user and
            is_authenticated(request.user) and
            request.user.is_staff
        )
