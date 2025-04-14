from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet, Count
from rest_framework.exceptions import ValidationError, PermissionDenied
from typing import Dict, Any, Optional
from apps.reviews.models import Review

User = get_user_model()


class ReviewService:
    @staticmethod
    def create_review(data: Dict[str, Any], user: User) -> Review:
        """Создание нового отзыва."""
        try:
            with transaction.atomic():
                review = Review(
                    product=data['product'],
                    user=user,
                    value=data['value'],
                    text=data.get('text', ''),
                    image=data.get('image', None),
                )
                review.full_clean()
                review.save()
                return review
        except Exception as e:
            raise ValidationError(f"Ошибка создания отзыва: {str(e)}")

    @staticmethod
    def update_review(review: Review, data: Dict[str, Any], user: User) -> Review:
        """Обновление существующего отзыва."""
        if review.user != user:
            raise PermissionDenied("Вы не автор отзыва.")
        allowed_fields = {'text', 'value'}
        data_to_update = {key: value for key, value in data.items() if key in allowed_fields}
        try:
            with transaction.atomic():
                for field, value in data_to_update.items():
                    setattr(review, field, value)
                review.full_clean()
                review.save()
                return review
        except Exception as e:
            raise ValidationError(f"Ошибка обновления отзыва: {str(e)}")

    @staticmethod
    def apply_ordering(queryset: QuerySet[Review], ordering: Optional[str]) -> QuerySet[Review]:
        if ordering == 'likes':
            return queryset.annotate(like_count=Count('likes')).order_by('like_count')
        elif ordering == '-likes':
            return queryset.annotate(like_count=Count('likes')).order_by('-like_count')
        elif ordering:
            return queryset.order_by(ordering)
        return queryset.order_by('-created')
