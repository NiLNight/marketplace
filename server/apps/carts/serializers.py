from rest_framework import serializers
from apps.carts.models import OrderItem
from apps.products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True, required=False)
    product = ProductListSerializer()
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']
