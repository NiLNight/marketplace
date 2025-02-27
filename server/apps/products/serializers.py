from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from apps.products.models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title', 'slug')


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
        fields = (
            'id', 'title', 'price', 'price_with_discount', 'in_stock',
            'rating_avg', 'popularity_score', 'thumbnail', 'created', 'category',
        )


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


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
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
            'category', 'thumbnail', 'created',
            'rating_avg', 'owner', 'is_active'
        ]

    def get_owner(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
        }
