import logging
from decimal import Decimal
from rest_framework import serializers
from apps.products.models import Product, Category
from apps.products.exceptions import InvalidProductData, ProductServiceException
from apps.products.services.product_services import ProductServices
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для отображения категорий.

    Поддерживает вложенные категории через children.
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'slug', 'description', 'parent', 'children']
        read_only_fields = ['slug']

    def get_children(self, obj: Category) -> list:
        """Получает дочерние категории.

        Args:
            obj: Объект Category.

        Returns:
            list: Список сериализованных дочерних категорий.
        """
        logger.debug(f"Retrieving children for category {obj.id}")
        try:
            # Используем cached_children для оптимизации запросов к базе данных
            queryset = obj.cached_children
            serializer = CategorySerializer(queryset, many=True)
            return serializer.data
        except Exception as e:
            logger.error(f"Failed to retrieve children for category {obj.id}: {str(e)}")
            return []


class ProductListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка продуктов.

    Включает основные поля и аннотации, такие как рейтинг и цена со скидкой.
    """
    rating_avg = serializers.FloatField(read_only=True)
    price_with_discount = serializers.SerializerMethodField()
    popularity_score = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'price', 'price_with_discount',
            'stock', 'rating_avg', 'popularity_score',
            'thumbnail', 'created', 'category', 'is_active'
        ]
        read_only_fields = ['id', 'created', 'rating_avg', 'popularity_score', 'is_active']

    def get_price_with_discount(self, obj: Product) -> Decimal:
        """Рассчитывает цену с учетом скидки.

        Args:
            obj: Объект Product.

        Returns:
            Decimal: Цена после скидки.
        """
        try:
            return obj.price * (1 - obj.discount / 100) if obj.discount else obj.price
        except Exception as e:
            logger.error(f"Failed to calculate price with discount for product {obj.id}: {str(e)}")
            return obj.price


class ProductCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления продуктов.

    Включает валидацию validated_data.
    """
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'discount',
            'stock', 'thumbnail', 'category'
        ]
        extra_kwargs = {
            'discount': {
                'required': False,
                'default': 0,
                'min_value': Decimal(0),
                'max_value': Decimal(100),
                'help_text': "Процент скидки (0-100)"
            },
            'stock': {'min_value': 0}
        }

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверяет данные для создания или обновления продукта.

        Args:
            data: Данные для валидации.

        Returns:
            Проверенные данные.

        Raises:
            InvalidProductData: Если данные некорректны.
        """
        logger.debug(f"Validating product data: {data}")
        price = data.get('price')
        if price is not None and price <= 0:
            logger.warning(f"Invalid price: {price}")
            raise InvalidProductData("Цена должна быть больше нуля.")

        discount = data.get('discount', 0)
        if discount and price is not None:
            price_with_discount = price * (1 - discount / 100)
            if price_with_discount < Decimal('0.01'):
                logger.warning(f"Price with discount too low: {price_with_discount}")
                raise InvalidProductData("Цена со скидкой не может быть меньше 0.01.")

        return data


class ProductDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения продукта.

    Включает категорию, владельца и цену со скидкой.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        help_text="ID категории для обновления"
    )
    rating_avg = serializers.FloatField(read_only=True)
    price_with_discount = serializers.SerializerMethodField()
    owner = serializers.SlugRelatedField(
        source='user',
        read_only=True,
        slug_field='username'
    )
    has_user_reviewed = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'price_with_discount',
            'stock', 'discount', 'category', 'category_id', 'thumbnail',
            'created', 'rating_avg', 'owner', 'is_active', 'has_user_reviewed'
        ]
        read_only_fields = ['id', 'created', 'owner', 'rating_avg']

    def get_price_with_discount(self, obj: Product) -> Decimal:
        """Рассчитывает цену с учетом скидки.

        Args:
            obj: Объект Product.

        Returns:
            Decimal: Цена после скидки.
        """
        try:
            return obj.price * (1 - obj.discount / 100) if obj.discount else obj.price
        except Exception as e:
            logger.error(f"Failed to calculate price with discount for product {obj.id}: {str(e)}")
            return obj.price

    def get_has_user_reviewed(self, obj: Product) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.reviews.filter(user=request.user).exists()

    def update(self, instance: Product, validated_data: Dict[str, Any]) -> Product:
        """Обновляет продукт через сервис ProductServices.

        Args:
            instance: Объект Product.
            validated_data: Проверенные данные.

        Returns:
            Product: Обновленный объект Product.

        Raises:
            InvalidProductData: Если обновление не удалось из-за некорректных данных или ошибки сервиса.
        """
        user = self.context['request'].user
        logger.info(f"Updating product {instance.id} via serializer, user={user.id}")
        try:
            return ProductServices.update_product(instance, validated_data, user)
        except ProductServiceException as e:
            logger.error(f"Failed to update product {instance.id}: {str(e)}")
            raise InvalidProductData(str(e))
