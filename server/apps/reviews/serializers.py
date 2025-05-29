import logging
from rest_framework import serializers
from apps.reviews.models import Review
from apps.reviews.exceptions import InvalidReviewData
from apps.products.models import Product

logger = logging.getLogger(__name__)


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения отзывов.

    Преобразует объекты Review в JSON, включая данные о продукте, пользователе и лайках.

    Attributes:
        user: Имя пользователя-автора отзыва.
        product: Название продукта.
        likes_count: Количество лайков отзыва.
    """
    user = serializers.StringRelatedField()
    product = serializers.StringRelatedField()
    likes_count = serializers.IntegerField()

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'value', 'text', 'image', 'created', 'updated', 'likes_count']
        read_only_fields = ['id', 'user', 'created', 'updated', 'likes_count']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления отзывов.

    Проверяет данные для создания или обновления отзыва, включая изображения. Поле product обязательно только для создания.
    """
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        required=False
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Review
        fields = ['product', 'value', 'text', 'image']
        read_only_fields = []

    def validate(self, attrs):
        """Проверяет данные для создания или обновления отзыва.

        Args:
            attrs: Данные для валидации.

        Returns:
            dict: Проверенные данные для создания или обновления отзыва.

        Raises:
            InvalidReviewData: Если данные некорректны (например, оценка вне диапазона, слишком длинный текст или неподдерживаемый формат изображения).
        """
        logger.debug(f"Validating review data: {attrs}")
        # Проверяем product только при создании (если это не частичное обновление)
        if not self.partial and 'product' not in attrs:
            logger.warning("Product field is required for review creation")
            raise InvalidReviewData("Поле product обязательно для создания отзыва.")

        value = attrs.get('value')
        if value is not None and (not isinstance(value, int) or value < 1 or value > 5):
            logger.warning(f"Invalid review value: {value}")
            raise InvalidReviewData("Оценка должна быть числом от 1 до 5.")

        text = attrs.get('text', '')
        if text and len(text.strip()) > 1000:
            logger.warning(f"Review text exceeds 1000 characters")
            raise InvalidReviewData("Текст отзыва не должен превышать 1000 символов.")

        image = attrs.get('image')
        if image:
            # Проверяем размер и формат изображения для предотвращения загрузки больших или неподдерживаемых файлов
            max_size = 5 * 1024 * 1024  # 5 MB
            if image.size > max_size:
                logger.warning(f"Image size {image.size} exceeds {max_size}")
                raise InvalidReviewData("Изображение не должно превышать 5 МБ.")

            allowed_formats = ['image/jpeg', 'image/png']
            if image.content_type not in allowed_formats:
                logger.warning(f"Invalid image format: {image.content_type}")
                raise InvalidReviewData("Изображение должно быть в формате JPEG или PNG.")
        return attrs
