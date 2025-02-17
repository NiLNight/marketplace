from rest_framework import serializers
from apps.products.models import Product, Category


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, obj):
        serializer = self.parent.parent.__class__(obj, context=self.context)
        return serializer.data


class CategorySerializer(serializers.ModelSerializer):
    children = RecursiveSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'title', 'slug', 'parent', 'children')


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    rating_avg = serializers.FloatField(read_only=True)
    price_with_discount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Product
        fields = ('id', 'title', 'price', 'rating_avg', 'thumbnail', 'price_with_discount')
