import logging
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Count
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from typing import Dict, Any, Optional
from apps.reviews.models import Review
from apps.reviews.exceptions import InvalidReviewData
from django.core.cache import cache

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewService:
    """Сервис для управления отзывами пользователей о продуктах."""
    ALLOWED_ORDERING_FIELDS = ['created', '-created', 'likes', '-likes']

    @staticmethod
    def create_review(data: Dict[str, Any], user: User) -> Review:
        """Создает новый отзыв для продукта.

        Args:
            data (dict): Данные для создания отзыва.
            user: Пользователь, создающий отзыв.

        Returns:
            Review: Созданный отзыв.

        Raises:
            InvalidReviewData: Если данные некорректны.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Creating review for product={data['product'].id}, user={user_id}")
        try:
            with transaction.atomic():
                instance = Review(
                    user=user,
                    product=data['product'],
                    value=data['value'],
                    text=data.get('text', ''),
                    image=data.get('image')
                )
                instance.full_clean()
                instance.save()
                cache.delete(f'reviews:{instance.pk}')
                logger.info(f"Created Review {instance.pk}, user={user_id}")
                return instance
        except Exception as e:
            logger.error(f"Failed to create Review: {str(e)}, user={user_id}")
            raise InvalidReviewData(f"Ошибка создания отзыва: {str(e)}")

    @staticmethod
    def update_review(review: Review, data: Dict[str, Any], user: User) -> Review:
        """Обновляет существующий отзыв.

        Args:
            review: Отзыв для обновления.
            data (dict): Данные для обновления.
            user: Пользователь, обновляющий отзыв.

        Returns:
            Review: Обновленный отзыв.

        Raises:
            PermissionDenied: Если пользователь не является автором.
            InvalidReviewData: Если обновление не удалось.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Updating review {review.id}, user={user_id}")
        if review.user != user:
            logger.warning(f"Permission denied for Review {review.id}, user={user_id}")
            raise PermissionDenied("Только автор может обновить отзыв.")
        try:
            with transaction.atomic():
                allowed_fields = {'text', 'value'}
                data_to_update = {key: value for key, value in data.items() if key in allowed_fields}
                for field, value in data_to_update.items():
                    setattr(review, field, value)
                review.full_clean()
                review.save()
                cache.delete(f'reviews:{review.pk}')
                logger.info(f"Updated Review {review.id}, user={user_id}")
                return review
        except Exception as e:
            logger.error(f"Failed to update Review {review.id}: {str(e)}, user={user_id}")
            raise InvalidReviewData(f"Ошибка обновления отзыва: {str(e)}")

    @staticmethod
    def apply_ordering(queryset: QuerySet[Review], ordering: Optional[str]) -> QuerySet[Review]:
        """Применяет сортировку к списку отзывов.

        Args:
            queryset: Набор отзывов для сортировки.
            ordering: Поле для сортировки.

        Returns:
            QuerySet: Отсортированный набор отзывов.
        """
        user_id = 'anonymous'  # Нет пользователя в этом контексте
        if ordering not in ReviewService.ALLOWED_ORDERING_FIELDS:
            ordering = '-created'
            logger.debug(f"Invalid ordering, defaulting to {ordering}, user={user_id}")
        if ordering in ['likes', '-likes']:
            logger.debug(f"Ordering reviews by {ordering}, user={user_id}")
            return queryset.annotate(like_count=Count('likes')).order_by(ordering.replace('likes', 'like_count'))
        return queryset.order_by(ordering)
