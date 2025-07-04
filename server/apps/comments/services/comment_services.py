import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from rest_framework.exceptions import PermissionDenied
from typing import Dict, Any, List
from apps.comments.models import Comment
from apps.comments.exceptions import CommentNotFound, InvalidCommentData
from apps.reviews.models import Review
from mptt.utils import get_cached_trees

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentService:
    """Сервис для управления комментариями к отзывам.

    Обрабатывает создание, получение, обновление и удаление комментариев с кэшированием и проверкой прав.

    Attributes:
        None: Класс не содержит статических атрибутов, только методы.
    """

    @staticmethod
    def _validate_comment_data(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Проверяет корректность данных для создания или обновления комментария.

        Args:
            data (Dict[str, Any]): Данные для комментария (отзыв, текст, родительский комментарий).
            user_id (str): ID пользователя или 'anonymous'.

        Returns:
            Dict[str, Any]: Проверенные данные с объектом Review.

        Raises:
            InvalidCommentData: Если данные некорректны (пустой текст, неверный отзыв или родитель).
        """
        if not data.get('text') or not data['text'].strip():
            logger.warning(f"Empty comment text, user={user_id}")
            raise InvalidCommentData("Текст комментария не может быть пустым.")

        review = data.get('review')
        if isinstance(review, int):
            try:
                review = Review.objects.get(pk=review)
            except Review.DoesNotExist:
                logger.warning(f"Review {review} not found, user={user_id}")
                raise InvalidCommentData("Указанный отзыв не существует.")
        elif not isinstance(review, Review):
            logger.warning(f"Invalid review type {type(review)}, user={user_id}")
            raise InvalidCommentData("Поле review должно быть ID или объектом Review.")

        parent = data.get('parent')
        validated_data = {'review': review, 'text': data['text'], 'parent': None}
        if parent:
            try:
                parent_comment = parent if isinstance(parent, Comment) else Comment.objects.get(pk=int(parent))
                if parent_comment.review_id != review.id:
                    logger.warning(
                        f"Parent comment {parent_comment.id} does not belong to review {review.id}, user={user_id}")
                    raise InvalidCommentData("Родительский комментарий должен относиться к тому же отзыву.")
                validated_data['parent'] = parent_comment
            except (Comment.DoesNotExist, ValueError):
                logger.warning(f"Invalid parent comment {parent}, user={user_id}")
                raise InvalidCommentData("Указанный родительский комментарий не существует.")

        return validated_data

    @staticmethod
    def get_comments(review_id: int, request: Any) -> List[Comment]:
        """Получает список комментариев для отзыва.

        Args:
            review_id (int): ID отзыва.
            request (Any): Объект запроса с параметрами сортировки.

        Returns:
            List[Comment]: Список комментариев.

        Raises:
            CommentNotFound: Если отзыв не найден или произошла ошибка при получении комментариев.
        """
        try:
            if not Review.objects.filter(pk=review_id).exists():
                logger.warning(f"Review {review_id} not found")
                raise CommentNotFound("Указанный отзыв не существует.")

            ordering = request.GET.get('ordering', 'created')  # По умолчанию по дате создания
            allowed_orderings = ['created', '-created', 'likes_count', '-likes_count']
            if ordering not in allowed_orderings:
                logger.warning(f"Invalid ordering {ordering} for review={review_id}")
                ordering = 'created'

            # Получаем все комментарии для отзыва
            comments = Comment.objects.prefetch_related('children', 'user', 'likes').filter(
                review_id=review_id
            )

            # Аннотируем likes_count для сортировки
            if 'likes_count' in ordering:
                comments = comments.annotate(likes_count=Count('likes'))

            # Применяем сортировку
            comments = comments.order_by(ordering)

            if not comments.exists():
                logger.info(f"No comments found for review={review_id}")
                return []

            # Получаем дерево комментариев
            root_nodes = get_cached_trees(comments)
            logger.info(f"Retrieved {len(root_nodes)} root comments for review={review_id}")
            return root_nodes

        except Exception as e:
            logger.error(f"Error retrieving comments for review={review_id}: {str(e)}")
            raise CommentNotFound(f"Ошибка получения комментариев: {str(e)}")

    @staticmethod
    @transaction.atomic
    def create_comment(data: Dict[str, Any], user: User) -> Comment:
        """Создает новый комментарий к отзыву.

        Проверяет и сохраняет комментарий, инвалидируя кэш комментариев отзыва.

        Args:
            data (Dict[str, Any]): Данные для создания комментария (отзыв, текст, родительский комментарий).
            user (User): Пользователь, создающий комментарий.

        Returns:
            Comment: Созданный объект комментария.

        Raises:
            InvalidCommentData: Если данные некорректны или произошла ошибка при создании.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Creating comment for review={data.get('review')}, user={user_id}")
        try:
            validated_data = CommentService._validate_comment_data(data, user_id)
            comment = Comment(
                user=user,
                review=validated_data['review'],
                text=validated_data['text'],
                parent=validated_data.get('parent')
            )
            comment.full_clean()
            comment.save()
            logger.info(f"Created Comment {comment.id}, user={user_id}")
            return comment

        except Exception as e:
            logger.error(f"Failed to create Comment: {str(e)}, data={data}, user={user_id}")
            raise InvalidCommentData(f"Ошибка создания комментария: {str(e)}")

    @staticmethod
    @transaction.atomic
    def update_comment(comment_id: int, data: Dict[str, Any], user: User) -> Comment:
        """Обновляет существующий комментарий.

        Проверяет, что только автор может обновить комментарий, и валидирует данные.

        Args:
            comment_id (int): ID комментария для обновления.
            data (Dict[str, Any]): Данные для обновления (например, текст).
            user (User): Пользователь, пытающийся обновить комментарий.

        Returns:
            Comment: Обновленный объект комментария.

        Raises:
            CommentNotFound: Если комментарий не существует.
            PermissionDenied: Если пользователь не является автором комментария.
            InvalidCommentData: Если данные некорректны или произошла ошибка.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Updating comment {comment_id}, user={user_id}")

        try:
            comment = Comment.objects.get(pk=comment_id)
            if comment.user != user:
                logger.warning(f"Permission denied for Comment {comment_id}, user={user_id}")
                raise PermissionDenied("Только автор может обновить комментарий.")
            # Проверка и преобразование входных данных
            if not data.get('text') or not data['text'].strip():
                logger.warning(f"Empty comment text for update, user={user_id}")
                raise InvalidCommentData("Текст комментария не может быть пустым.")

            allowed_fields = {'text'}
            data_to_update = {key: value for key, value in data.items() if key in allowed_fields}
            for field, value in data_to_update.items():
                setattr(comment, field, value)
            comment.full_clean()
            comment.save()
            logger.info(f"Updated Comment {comment_id}, user={user_id}")
            return comment

        except Comment.DoesNotExist:
            logger.warning(f"Comment {comment_id} not found, user={user_id}")
            raise CommentNotFound()
        except PermissionDenied:
            raise
        except Exception as e:
            logger.error(f"Failed to update Comment {comment_id}: {str(e)}, data={data}, user={user_id}")
            raise InvalidCommentData(f"Ошибка обновления комментария: {str(e)}")

    @staticmethod
    @transaction.atomic
    def delete_comment(comment_id: int, user: User) -> None:
        """Удаляет комментарий.

        Проверяет, что только автор может удалить комментарий, и инвалидирует кэш.

        Args:
            comment_id (int): ID комментария для удаления.
            user (User): Пользователь, пытающийся удалить комментарий.

        Raises:
            CommentNotFound: Если комментарий не существует.
            PermissionDenied: Если пользователь не является автором комментария.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Deleting comment {comment_id}, user={user_id}")

        try:
            comment = Comment.objects.get(pk=comment_id)
            if comment.user != user:
                logger.warning(f"Permission denied for Comment {comment_id}, user={user_id}")
                raise PermissionDenied("Только автор может удалить комментарий.")
            comment.delete()
            logger.info(f"Deleted Comment {comment_id}, user={user_id}")

        except Comment.DoesNotExist:
            logger.warning(f"Comment {comment_id} not found, user={user_id}")
            raise CommentNotFound()
