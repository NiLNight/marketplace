import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from typing import Dict, Any
from apps.comments.models import Comment
from apps.comments.exceptions import InvalidCommentData
from django.core.cache import cache

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentService:
    """Сервис для управления комментариями к отзывам."""

    @staticmethod
    def create_comment(data: Dict[str, Any], user: User) -> Comment:
        """Создает новый комментарий к отзыву.

        Args:
            data (dict): Данные для создания комментария.
            user: Пользователь, создающий комментарий.

        Returns:
            Comment: Созданный комментарий.

        Raises:
            InvalidCommentData: Если данные некорректны.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Creating comment for review={data['review'].id}, user={user_id}")
        try:
            with transaction.atomic():
                comment = Comment(
                    user=user,
                    review=data['review'],
                    text=data['text'],
                    parent=data.get('parent')
                )
                comment.full_clean()
                comment.save()
                cache.delete(f'comments:{comment.review_id}')
                logger.info(f"Created Comment {comment.id}, user={user_id}")
                return comment
        except Exception as e:
            logger.error(f"Failed to create Comment: {str(e)}, user={user_id}")
            raise InvalidCommentData(f"Ошибка создания комментария: {str(e)}")

    @staticmethod
    def update_comment(comment: Comment, data: Dict[str, Any], user: User) -> Comment:
        """Обновляет существующий комментарий.

        Args:
            comment: Комментарий для обновления.
            data (dict): Данные для обновления.
            user: Пользователь, обновляющий комментарий.

        Returns:
            Comment: Обновленный комментарий.

        Raises:
            PermissionDenied: Если пользователь не является автором.
            InvalidCommentData: Если обновление не удалось.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Updating comment {comment.id}, user={user_id}")
        if comment.user != user:
            logger.warning(f"Permission denied for Comment {comment.id}, user={user_id}")
            raise PermissionDenied("Только автор может обновить комментарий.")
        try:
            with transaction.atomic():
                allowed_fields = {'text'}
                data_to_update = {key: value for key, value in data.items() if key in allowed_fields}
                for field, value in data_to_update.items():
                    setattr(comment, field, value)
                comment.full_clean()
                comment.save()
                cache.delete(f'comments:{comment.review_id}')
                logger.info(f"Updated Comment {comment.id}, user={user_id}")
                return comment
        except Exception as e:
            logger.error(f"Failed to update Comment {comment.id}: {str(e)}, user={user_id}")
            raise InvalidCommentData(f"Ошибка обновления комментария: {str(e)}")
