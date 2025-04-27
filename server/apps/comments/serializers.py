import logging
from rest_framework import serializers
from apps.comments.models import Comment
from apps.comments.exceptions import InvalidCommentData
from apps.reviews.models import Review

logger = logging.getLogger(__name__)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения комментариев.

    Преобразует объекты Comment в JSON, включая дочерние комментарии и количество лайков.

    Атрибуты:
        user (StringRelatedField): Имя пользователя-автора комментария.
        children (SerializerMethodField): Вложенные дочерние комментарии.
        likes_count (SerializerMethodField): Количество лайков комментария.
    """
    user = serializers.StringRelatedField()
    children = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'parent', 'created', 'updated', 'children', 'likes_count']
        read_only_fields = ['id', 'user', 'created', 'updated', 'children', 'likes_count']

    def get_children(self, obj):
        """Получает дочерние комментарии.

        Args:
            obj (Comment): Объект комментария.

        Returns:
            list: Сериализованные данные дочерних комментариев.
        """
        queryset = obj.cached_children
        serializer = CommentSerializer(queryset, many=True)
        return serializer.data

    def get_likes_count(self, obj) -> int:
        """Подсчитывает количество лайков комментария.

        Args:
            obj (Comment): Объект комментария.

        Returns:
            int: Общее количество лайков.
        """
        return obj.likes.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания комментариев.

    Проверяет и обрабатывает данные для создания новых комментариев.
    """
    review = serializers.PrimaryKeyRelatedField(queryset=Review.objects.all())

    class Meta:
        model = Comment
        fields = ['review', 'text', 'parent']
        read_only_fields = []

    def validate(self, attrs):
        """Проверяет данные для создания комментария.

        Убеждается, что текст комментария не пустой и отзыв существует.

        Args:
            attrs (dict): Данные для проверки.

        Returns:
            dict: Проверенные данные.

        Raises:
            InvalidCommentData: Если текст комментария пустой или отзыв некорректен.
        """
        logger.debug(f"Validating comment creation data: {attrs}")
        if not attrs['text'].strip():
            logger.warning("Empty comment text")
            raise InvalidCommentData("Текст комментария не может быть пустым.")
        return attrs
