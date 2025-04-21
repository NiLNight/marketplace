from rest_framework import serializers
from apps.wishlists.models import WishlistItem
from apps.products.serializers import ProductListSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов списка желаний."""
    product = ProductListSerializer()

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'created', 'updated']
