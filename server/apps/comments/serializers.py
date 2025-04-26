import logging
from rest_framework import serializers
from apps.comments.models import Comment
from apps.comments.exceptions import InvalidCommentData

logger = logging.getLogger(__name__)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения комментариев.

    Преобразует объекты Comment в JSON, включая дочерние комментарии и лайки.
    """
    user = serializers.StringRelatedField()
    children = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'parent', 'created', 'updated', 'children', 'likes_count']
        read_only_fields = ['id', 'user', 'created', 'updated', 'children', 'likes_count']

    def get_children(self, obj):
        """Возвращает дочерние комментарии.

        Args:
            obj: Объект комментария.

        Returns:
            list: Сериализованные дочерние комментарии.
        """
        queryset = obj.cached_children
        serializer = CommentSerializer(queryset, many=True)
        return serializer.data

    def get_likes_count(self, obj) -> int:
        """Возвращает количество лайков для комментария.

        Args:
            obj: Объект комментария.

        Returns:
            int: Количество лайков.
        """
        return obj.likes.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания комментариев."""

    class Meta:
        model = Comment
        fields = ['review', 'text', 'parent']
        read_only_fields = []

    def validate(self, attrs):
        """Проверка данных для создания комментария.

        Args:
            attrs (dict): Данные для создания комментария.

        Returns:
            dict: Валидированные данные.

        Raises:
            InvalidCommentData: Если данные некорректны.
        """
        logger.debug(f"Validating comment creation data: {attrs}")
        if not attrs['text'].strip():
            logger.warning("Empty comment text")
            raise InvalidCommentData("Текст комментария не может быть пустым.")
        return attrs
