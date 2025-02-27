from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Разрешение для владельца или администратора"""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_stuff
