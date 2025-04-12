from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.reviews.models import Review


class ReviewService:
    @staticmethod
    def create_review(data, user):
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