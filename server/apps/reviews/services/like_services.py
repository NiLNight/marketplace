from typing import Dict

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from apps.reviews.models import Review, ReviewLike, Comment, CommentLike

User = get_user_model()


class LikeService:
    @staticmethod
    def toggle_review_like(review: Review, user: User) -> Dict[str, str]:
        """Переключает лайк для обзора, без ограничений на собственные записи."""
        try:
            like, created = ReviewLike.objects.get_or_create(review=review, user=user)
            if not created:
                like.delete()
                return {'action': 'unliked'}
            return {'action': 'liked'}
        except IntegrityError:
            raise ValidationError('Ошибка при обработке лайка.')

    @staticmethod
    def toggle_comment_like(comment: Comment, user: User) -> Dict[str, str]:
        """Переключает лайк для комментария, без ограничений на собственные записи."""
        try:
            like, created = CommentLike.objects.get_or_create(comment=comment, user=user)
            if not created:
                like.delete()
                return {'action': 'unliked'}
            return {'action': 'liked'}
        except IntegrityError:
            raise ValidationError("Ошибка при обработке лайка.")