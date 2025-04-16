from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Count
from typing import Dict, Any, Optional
from apps.reviews.models import Review
from apps.reviews.services.base_service import BaseService

User = get_user_model()


class ReviewService(BaseService):
    ALLOWED_ORDERING_FIELDS = ['created', '-created', 'likes', '-likes']

    @staticmethod
    def create_review(data: Dict[str, Any], user: User) -> Review:
        """Создание нового отзыва."""
        return BaseService.create_instance(
            model_class=Review,
            data=data,
            user=user,
            cache_key_prefix='reviews',
            product=data['product']
        )

    @staticmethod
    def update_review(review: Review, data: Dict[str, Any], user: User) -> Review:
        """Обновление существующего отзыва."""
        return BaseService.update_instance(
            instance=review,
            data=data,
            user=user,
            allowed_fields={'text', 'value'},
            cache_key_prefix='reviews'
        )

    @staticmethod
    def apply_ordering(queryset: QuerySet[Review], ordering: Optional[str]) -> QuerySet[Review]:
        """Применяет сортировку к queryset отзывов."""
        if ordering not in ReviewService.ALLOWED_ORDERING_FIELDS:
            ordering = '-created'  # Значение по умолчанию
        if ordering in ['likes', '-likes']:
            return queryset.annotate(like_count=Count('likes')).order_by(ordering.replace('likes', 'like_count'))
        return queryset.order_by(ordering)
