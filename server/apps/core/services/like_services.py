import logging
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.contrib.contenttypes.models import ContentType
from typing import Dict, Any
from apps.core.models import Like
from apps.reviews.exceptions import InvalidReviewData, ReviewNotFound

User = get_user_model()
logger = logging.getLogger(__name__)


class LikeService:
    """Сервис для управления лайками к различным сущностям.

    Предоставляет методы для переключения состояния лайков с атомарными операциями и инвалидацией кэша.
    """

    @staticmethod
    @transaction.atomic
    def toggle_like(content_type: ContentType, object_id: int, user: User) -> Dict[str, Any]:
        """Переключает состояние лайка для указанной сущности.

        Создает лайк, если его нет, или удаляет существующий для указанного пользователя и объекта.

        Args:
            content_type (ContentType): Тип сущности (например, Review или Comment).
            object_id (int): ID объекта (например, ID отзыва или комментария).
            user (User): Пользователь, выполняющий действие.

        Returns:
            Dict[str, Any]: Словарь с действием ('liked' или 'unliked') и дополнительной информацией (например, product_id).

        Raises:
            ReviewNotFound: Если объект не существует.
            InvalidReviewData: Если произошла ошибка целостности данных.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Toggling like for {content_type.model}:{object_id}, user={user_id}")

        try:
            # Проверка существования объекта
            try:
                content_type.get_object_for_this_type(pk=object_id)
            except content_type.model_class().DoesNotExist:
                logger.warning(f"{content_type.model} {object_id} not found, user={user_id}")
                raise ReviewNotFound(f"{content_type.model} с ID {object_id} не найден.")

            # Попытка получить или создать лайк
            like, created = Like.objects.get_or_create(
                content_type=content_type,
                object_id=object_id,
                user=user
            )

            additional_data = {}
            if not created:
                # Если лайк уже существует, удаляем его
                like.delete()
                action = 'unliked'
                logger.info(f"Unliked {content_type.model}:{object_id}, user={user_id}")
            else:
                # Если лайк создан, отмечаем как поставленный
                action = 'liked'
                logger.info(f"Liked {content_type.model}:{object_id}, user={user_id}")

            return {'action': action, **additional_data}

        except IntegrityError as e:
            logger.error(
                f"Integrity error toggling like for {content_type.model}:{object_id}: {str(e)}, user={user_id}")
            raise InvalidReviewData("Ошибка обработки лайка")
