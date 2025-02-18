from rest_framework import serializers
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
