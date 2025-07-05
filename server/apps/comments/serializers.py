import logging
from rest_framework import serializers
from apps.comments.models import Comment
from apps.comments.exceptions import InvalidCommentData
from apps.reviews.models import Review
from apps.users.serializers import UserSerializer

logger = logging.getLogger(__name__)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения комментариев.

    Преобразует объекты Comment в JSON, включая дочерние комментарии и количество лайков.

    Attributes:
        user: Имя пользователя-автора комментария.
        children: Вложенные дочерние комментарии.
        likes_count: Количество лайков комментария.
    """
    user = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    def get_children(self, obj):
        """Получает дочерние комментарии.

        Args:
            obj (Comment): Объект комментария.

        Returns:
            list: Сериализованные данные дочерних комментариев.

        Raises:
            Exception: Если произошла ошибка при получении дочерних комментариев из-за проблем с базой данных.
        """
        queryset = obj.cached_children
        serializer = CommentSerializer(queryset, many=True, context=self.context)
        return serializer.data

    def get_likes_count(self, obj) -> int:
        """Подсчитывает количество лайков комментария.

        Args:
            obj (Comment): Объект комментария.

        Returns:
            int: Общее количество лайков.

        Raises:
            Exception: Если произошла ошибка при подсчете лайков из-за проблем с базой данных.
        """
        return obj.likes.count()

    def get_is_liked(self, obj) -> bool:
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

    class Meta:
        model = Comment
        fields = ['id', 'review', 'user', 'text', 'parent', 'created', 'updated', 'children', 'likes_count', 'is_liked']
        read_only_fields = ['id', 'user', 'created', 'updated', 'children', 'likes_count']


class CommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания комментариев.

    Проверяет и обрабатывает данные для создания новых комментариев.

    Attributes:
        review: Отзыв, к которому относится комментарий.
        text: Текст комментария.
        parent: Родительский комментарий (опционально).
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
            InvalidCommentData: Если текст комментария пустой или отзыв не существует либо неактивен.
        """
        logger.debug(f"Validating comment creation data: {attrs}")
        if not attrs['text'].strip():
            logger.warning("Empty comment text")
            raise InvalidCommentData("Текст комментария не может быть пустым.")
        return attrs
