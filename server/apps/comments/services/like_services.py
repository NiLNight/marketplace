import logging
from typing import Dict
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.cache import cache
from apps.comments.exceptions import CommentException
from apps.comments.models import CommentLike

User = get_user_model()
logger = logging.getLogger(__name__)


class LikeService:
    """Сервис для управления лайками к комментариям."""

    @staticmethod
    def toggle_like(instance, user: User) -> Dict[str, str]:
        """Переключает состояние лайка для комментария.

        Создает лайк, если его нет, или удаляет существующий.

        Args:
            instance: Экземпляр комментария.
            user: Пользователь, ставящий лайк.

        Returns:
            dict: Результат операции ('liked' или 'unliked').

        Raises:
            CommentException: Если операция не удалась.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Toggling like for Comment {instance.id}, user={user_id}")
        try:
            like, created = CommentLike.objects.get_or_create(review=instance, user=user)
            if not created:
                like.delete()
                action = 'unliked'
                logger.info(f"Unliked Comment {instance.id}, user={user_id}")
            else:
                action = 'liked'
                logger.info(f"Liked Comment {instance.id}, user={user_id}")
            cache.delete(f'comments:{instance.review_id}')
            return {'action': action}
        except IntegrityError as e:
            logger.error(f"Integrity error toggling like for Comment {instance.id}: {str(e)}, user={user_id}")
            raise CommentException("Ошибка при обработке лайка")
