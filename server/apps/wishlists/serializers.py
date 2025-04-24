from rest_framework import serializers
from apps.wishlists.models import WishlistItem
from apps.products.serializers import ProductListSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов списка желаний.

    Преобразует объекты WishlistItem в JSON и обратно, включая данные о товаре и временные метки.
    Используется для API-ответов, отображающих содержимое списка желаний.
    """
    id = serializers.IntegerField(
        read_only=True,
        help_text='Уникальный идентификатор элемента списка желаний.'
    )
    product = ProductListSerializer(
        read_only=True,
        help_text='Данные о товаре, добавленном в список желаний.'
    )
    created = serializers.DateTimeField(
        read_only=True,
        help_text='Дата и время добавления товара в список желаний.'
    )
    updated = serializers.DateTimeField(
        read_only=True,
        help_text='Дата и время последнего обновления элемента.'
    )

    class Meta:
        """Метаданные сериализатора WishlistItemSerializer.

        Определяет модель, сериализуемые поля и ограничения.
        """
        model = WishlistItem
        fields = ['id', 'product', 'created', 'updated']
        read_only_fields = ['id', 'product', 'created', 'updated']

    def validate(self, attrs):
        """Проверка корректности данных перед сериализацией.

        Проверяет, что товар активен (если применимо).

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если товар неактивен.
        """
        instance = self.instance
        if instance and not instance.product.is_active:
            raise serializers.ValidationError("Товар неактивен.")
        return attrs
