from rest_framework import serializers
from apps.carts.models import OrderItem
from apps.products.serializers import ProductDetailSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']
