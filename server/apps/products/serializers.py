from rest_framework import serializers, validators
from rest_framework.exceptions import ValidationError

from apps.products.models import Product, Category
from apps.products.exceptions import ProductServiceException
from apps.products.services.product_services import ProductServices


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['title', 'slug', 'description', 'parent', 'children']

    def get_children(self, obj):
        qs = obj.cached_children
        serializer = CategorySerializer(qs, many=True)
        return serializer.data


class ProductListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка продуктов с оптимизированными запросами
    """
    category = CategorySerializer()
    rating_avg = serializers.FloatField(read_only=True)
    price_with_discount = serializers.SerializerMethodField()
    popularity_score = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'price', 'price_with_discount',
            'stock', 'rating_avg', 'popularity_score',
            'thumbnail', 'created', 'category'
        ]
        select_related = ['category']  # Оптимизация запросов

    def get_price_with_discount(self, obj):
        """Динамический расчет цены со скидкой"""
        return obj.price * (1 - obj.discount / 100) if obj.discount else obj.price


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания продукта с расширенной валидацией
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'discount',
            'stock', 'category', 'thumbnail', 'user'
        ]
        extra_kwargs = {
            'category': {'required': True},
            'discount': {
                'required': False,
                'default': 0,
                'min_value': 0,
                'max_value': 100,
                'help_text': "Процент скидки (0-100)"
            },
            'stock': {'min_value': 0}
        }

    def validate(self, data):
        """Глобальная валидация данных"""
        if data['price'] <= 0:
            raise serializers.ValidationError(
                {"price": "Цена должна быть больше нуля"}
            )
        return data


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Детальный сериализатор продукта с безопасным обновлением
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

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'price_with_discount',
            'stock', 'discount', 'category', 'category_id', 'thumbnail',
            'created', 'rating_avg', 'owner', 'is_active'
        ]
        read_only_fields = ['is_active', 'created', 'owner']
        select_related = ['category', 'user']

    def get_price_with_discount(self, obj):
        """Динамический расчет цены со скидкой"""
        return obj.price * (1 - obj.discount / 100) if obj.discount else obj.price

    def update(self, instance, validated_data):
        """Безопасное обновление с обработкой ошибок"""
        try:
            return ProductServices.update_product(instance, validated_data)
        except ProductServiceException as e:
            raise serializers.ValidationError(
                {"non_field_errors": [str(e)]}
            ) from e
        except ValidationError as e:
            raise serializers.ValidationError(e)
