from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.reviews.models import Comment


class CommentService:
    @staticmethod
    def create_comment(data, user):
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
