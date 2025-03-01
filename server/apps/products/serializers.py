from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from apps.products.services.product_services import ProductServices
from apps.products.models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    rating_avg = serializers.FloatField()
    price_with_discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    popularity_score = serializers.FloatField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'price', 'price_with_discount', 'in_stock',
            'rating_avg', 'popularity_score', 'thumbnail', 'created', 'category',
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price',
            'discount', 'stock', 'category',
            'thumbnail', 'user'
        ]
        extra_kwargs = {
            'category': {'required': True},
        }

    def validate_discount(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Скидка должна быть в диапазоне 0-100%")
        return value


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
        required=False
    )
    rating_avg = serializers.FloatField()
    price_with_discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price',
            'price_with_discount', 'stock', 'discount',
            'category', 'category_id', 'thumbnail', 'created',
            'rating_avg', 'owner', 'is_active'
        ]

    def get_owner(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
        }

    def update(self, instance, validated_data):
        try:
            return ProductServices.update_product(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(str(e))
