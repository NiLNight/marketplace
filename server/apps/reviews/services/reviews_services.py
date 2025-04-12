from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.reviews.models import Review

User = get_user_model()


class ReviewService:
    @staticmethod
    def create_review(data: dict, user: User):
        """Создание нового отзыва."""
        try:
            with transaction.atomic():
                review = Review(
                    product=data['product'],
                    user=user,
                    value=data['value'],
                    text=data.get('text', )
                )
                review.full_clean()
                review.save()
                return review
        except Exception as e:
            raise ValidationError(f"Ошибка создания отзыва: {str(e)}")

    @staticmethod
    def update_review(review, data: dict):
        """Обновление существующего отзыва."""
        try:
            with transaction.atomic():
                for field, value in data.items():
                    setattr(review, field, value)
                review.full_clean()
                review.save()
                return review
        except Exception as e:
            raise ValidationError(f"Ошибка обновления отзыва: {str(e)}")
