from typing import Dict, Any

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.reviews.models import Comment

User = get_user_model()


class CommentService:
    @staticmethod
    def create_comment(data: dict, user: User):
        """Создание нового комментария."""
        try:
            with transaction.atomic():
                comment = Comment(
                    review=data['review'],
                    user=user,
                    text=data['text'],
                    parent=data.get('parent', None)
                )
                comment.full_clean()
                comment.save()
                return comment
        except Exception as e:
            raise ValidationError(f"Ошибка создания комментария: {str(e)}")

    @staticmethod
    def update_comment(comment: Comment, data: Dict[str, Any], user: User):
        """Обновление комментария"""
        if comment.user != user:
            raise PermissionDenied("Вы не автор комментария.")
        allowed_fields = {'text'}
        data_to_update = {k: v for k, v in data.items() if k in allowed_fields}
        try:
            with transaction.atomic():
                for field, value in data_to_update.items():
                    setattr(comment, field, value)
                comment.full_clean()  # Валидация модели
                comment.save()
                return comment
        except Exception as e:
            raise ValidationError(f"Ошибка обновления комментария: {str(e)}")
