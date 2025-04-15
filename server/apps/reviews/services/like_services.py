from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from typing import Dict
from django.core.cache import cache
from apps.reviews.models import Review, ReviewLike, Comment, CommentLike

User = get_user_model()


class LikeService:
    @staticmethod
    def toggle_review_like(review: Review, user: User) -> Dict[str, str]:
        """Переключает лайк для обзора."""
        try:
            like, created = ReviewLike.objects.get_or_create(review=review, user=user)
            if not created:
                like.delete()
                action = 'unliked'
            else:
                action = 'liked'
            cache.delete(f'reviews_{review.product.id}')
            return {'action': action}
        except IntegrityError:
            raise ValidationError('Ошибка при обработке лайка.')

    @staticmethod
    def toggle_comment_like(comment: Comment, user: User) -> Dict[str, str]:
        """Переключает лайк для комментария."""
        try:
            like, created = CommentLike.objects.get_or_create(comment=comment, user=user)
            if not created:
                like.delete()
                action = 'unliked'
            else:
                action = 'liked'
            cache.delete(f'comments_{comment.review.id}')
            return {'action': action}
        except IntegrityError:
            raise ValidationError("Ошибка при обработке лайка.")
