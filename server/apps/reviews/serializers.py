import logging
from rest_framework import serializers
from apps.reviews.models import Review
from apps.reviews.exceptions import InvalidReviewData

logger = logging.getLogger(__name__)


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения отзывов.

    Преобразует объекты Review в JSON, включая данные о пользователе и лайках.
    """
    user = serializers.StringRelatedField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'value', 'text', 'image', 'created', 'updated', 'likes_count']
        read_only_fields = ['id', 'user', 'created', 'updated', 'likes_count']

    def get_likes_count(self, obj) -> int:
        """Возвращает количество лайков для отзыва.

        Args:
            obj: Объект отзыва.

        Returns:
            int: Количество лайков.
        """
        return obj.likes.count()

    def validate(self, attrs):
        """Проверка корректности данных перед сериализацией.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            InvalidReviewData: Если оценка вне диапазона 1-5.
        """
        logger.debug(f"Validating review data: {attrs}")
        if 'value' in attrs and (attrs['value'] < 1 or attrs['value'] > 5):
            logger.warning(f"Invalid review value {attrs['value']}")
            raise InvalidReviewData("Оценка должна быть от 1 до 5.")
        return attrs


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания отзывов."""

    class Meta:
        model = Review
        fields = ['product', 'value', 'text', 'image']
        read_only_fields = []

    def validate(self, attrs):
        """Проверка данных для создания отзыва.

        Args:
            attrs (dict): Данные для создания отзыва.

        Returns:
            dict: Валидированные данные.

        Raises:
            InvalidReviewData: Если оценка вне диапазона 1-5.
        """
        logger.debug(f"Validating review creation data: {attrs}")
        if attrs['value'] < 1 or attrs['value'] > 5:
            logger.warning(f"Invalid review value {attrs['value']}")
            raise InvalidReviewData("Оценка должна быть от 1 до 5.")
        return attrs
