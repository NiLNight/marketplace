import logging
from typing import Dict
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.cache import cache
from apps.reviews.exceptions import ReviewException
from apps.reviews.models import ReviewLike

User = get_user_model()
logger = logging.getLogger(__name__)


class LikeService:
    """Сервис для управления лайками к отзывам."""

    @staticmethod
    def toggle_like(instance, user: User) -> Dict[str, str]:
        """Переключает состояние лайка для отзыва.

        Создает лайк, если его нет, или удаляет существующий.

        Args:
            instance: Экземпляр отзыва.
            user: Пользователь, ставящий лайк.

        Returns:
            dict: Результат операции ('liked' или 'unliked').

        Raises:
            ReviewException: Если операция не удалась.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Toggling like for Review {instance.id}, user={user_id}")
        try:
            like, created = ReviewLike.objects.get_or_create(review=instance, user=user)
            if not created:
                like.delete()
                action = 'unliked'
                logger.info(f"Unliked Review {instance.id}, user={user_id}")
            else:
                action = 'liked'
                logger.info(f"Liked Review {instance.id}, user={user_id}")
            cache.delete(f'reviews:{instance.pk}')
            return {'action': action}
        except IntegrityError as e:
            logger.error(f"Integrity error toggling like for Review {instance.id}: {str(e)}, user={user_id}")
            raise ReviewException("Ошибка при обработке лайка")
