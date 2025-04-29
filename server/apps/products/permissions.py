import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsOwnerOrAdmin(BasePermission):
    """Разрешение для владельца продукта или администратора.

    Проверяет, является ли пользователь владельцем объекта или администратором.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        """Проверяет права доступа к объекту.

        Args:
            request: HTTP-запрос.
            view: Представление.
            obj: Объект для проверки (например, Product).

        Returns:
            True, если пользователь имеет доступ.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.debug(f"Checking permissions for user={user_id}, obj={obj}")
        has_permission = obj.user == request.user or request.user.is_staff
        if not has_permission:
            logger.warning(f"Permission denied for user={user_id}, obj={obj}")
        return has_permission
