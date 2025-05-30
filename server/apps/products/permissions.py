import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsOwnerOrAdmin(BasePermission):
    """Разрешение для владельца продукта или администратора.

    Проверяет, является ли пользователь владельцем объекта или администратором.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        """Проверяет, имеет ли пользователь права на доступ к объекту.

        Args:
            request: HTTP-запрос с информацией о пользователе.
            view: Представление, к которому осуществляется доступ.
            obj: Объект, к которому запрашивается доступ.

        Returns:
            bool: True, если пользователь является владельцем объекта или администратором, иначе False.
        """
        if not request.user.is_authenticated or not obj.user:
            logger.warning(f"Permission denied: User={request.user.id or 'anonymous'}, obj={obj}")
            return False
        has_permission = obj.user == request.user or request.user.is_staff
        if not has_permission:
            logger.warning(f"Permission denied for user={request.user.id}, obj={obj}")
        return has_permission
