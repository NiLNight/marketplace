import logging
from typing import Dict
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from apps.comments.models import Comment, CommentLike
from apps.comments.exceptions import CommentNotFound, LikeOperationFailed

User = get_user_model()
logger = logging.getLogger(__name__)


class LikeService:
    """Сервис для управления лайками комментариев.

    Предоставляет методы для переключения состояния лайков с атомарными операциями и инвалидацией кэша.
    """

    @staticmethod
    @transaction.atomic
    def toggle_like(comment_id: int, user: User) -> Dict[str, str]:
        """Переключает состояние лайка для комментария.

        Создает лайк, если его нет, или удаляет существующий для указанного пользователя и комментария.

        Args:
            comment_id (int): ID комментария для лайка или его снятия.
            user (User): Пользователь, выполняющий действие.

        Returns:
            Dict[str, str]: Словарь с действием ('liked' или 'unliked') и ID отзыва.

        Raises:
            CommentNotFound: Если комментарий с указанным ID не найден.
            LikeOperationFailed: Если произошла ошибка целостности данных.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Toggling like for Comment {comment_id}, user={user_id}")

        try:
            comment = Comment.objects.get(pk=comment_id)
            like, created = CommentLike.objects.get_or_create(comment=comment, user=user)
            if not created:
                like.delete()
                action = 'unliked'
                logger.info(f"Unliked Comment {comment_id}, user={user_id}")
            else:
                action = 'liked'
                logger.info(f"Liked Comment {comment_id}, user={user_id}")

            return {'action': action, 'review_id': comment.review_id}
        except Comment.DoesNotExist:
            logger.warning(f"Comment {comment_id} not found, user={user_id}")
            raise CommentNotFound()
        except IntegrityError as e:
            logger.error(f"Integrity error toggling like for Comment {comment_id}: {str(e)}, user={user_id}")
            raise LikeOperationFailed()
