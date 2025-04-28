import logging
from rest_framework import serializers
from apps.reviews.models import Review
from apps.reviews.exceptions import InvalidReviewData
from apps.products.models import Product
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения отзывов.

    Преобразует объекты Review в JSON, включая данные о пользователе, продукте и количестве лайков.

    Атрибуты:
        user (StringRelatedField): Имя пользователя-автора отзыва.
        product (StringRelatedField): Название продукта.
        likes_count (SerializerMethodField): Количество лайков отзыва.
    """
    user = serializers.StringRelatedField()
    product = serializers.StringRelatedField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'value', 'text', 'image', 'created', 'updated', 'likes_count']
        read_only_fields = ['id', 'user', 'created', 'updated', 'likes_count']

    def get_likes_count(self, obj) -> int:
        """Возвращает количество лайков для отзыва.

        Args:
            obj (Review): Объект отзыва.

        Returns:
            int: Количество лайков.
        """
        return obj.likes.count()


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления отзывов.

    Проверяет и обрабатывает данные для создания или обновления отзывов, включая изображения.
    """
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Review
        fields = ['product', 'value', 'text', 'image']
        read_only_fields = []

    def validate(self, attrs):
        """Проверяет данные для создания или обновления отзыва.

        Убеждается, что оценка корректна, продукт существует, текст не слишком длинный и изображение валидно.

        Args:
            attrs (dict): Данные для проверки.

        Returns:
            dict: Проверенные данные.

        Raises:
            InvalidReviewData: Если данные некорректны (оценка, текст, изображение).
        """
        logger.debug(f"Validating review creation data: {attrs}")
        value = attrs.get('value')
        if not isinstance(value, int) or value < 1 or value > 5:
            logger.warning(f"Invalid review value {value}")
            raise InvalidReviewData("Оценка должна быть целым числом от 1 до 5.")

        text = attrs.get('text', '')
        if text and len(text.strip()) > 1000:
            logger.warning("Review text too long")
            raise InvalidReviewData("Текст отзыва не должен превышать 1000 символов.")

        image = attrs.get('image')
        if image:
            # Проверка размера изображения
            max_size = 5 * 1024 * 1024  # 5 MB
            if image.size > max_size:
                logger.warning(f"Image size {image.size} exceeds limit {max_size}")
                raise InvalidReviewData("Изображение не должно превышать 5 МБ.")
        return attrs
