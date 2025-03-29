from rest_framework import serializers
from apps.orders.models import Order
from apps.carts.serializers import CartItemSerializer


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'total_price', 'created']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, source='order_items')

    class Meta:
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'items']
