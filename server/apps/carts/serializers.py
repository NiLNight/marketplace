from rest_framework import serializers
from apps.carts.models import OrderItem
from apps.products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов корзины.

    Преобразует объекты OrderItem в JSON и обратно, включая данные о товаре и количестве.
    Используется для API-ответов, отображающих содержимое корзины.
    """
    id = serializers.IntegerField(
        allow_null=True,
        required=False,
        read_only=True,
        help_text='Уникальный идентификатор элемента корзины (null для неавторизованных пользователей).'
    )
    product = ProductListSerializer(
        read_only=True,
        help_text='Данные о товаре, добавленном в корзину.'
    )
    quantity = serializers.IntegerField(
        min_value=1,
        max_value=20,
        help_text='Количество единиц товара в корзине (от 1 до 20).'
    )

    class Meta:
        """Метаданные сериализатора CartItemSerializer.

        Определяет модель, сериализуемые поля и ограничения.
        """
        model = OrderItem
        fields = ['id', 'product', 'quantity']
        read_only_fields = ['id', 'product']

    def validate(self, attrs):
        """Проверка корректности данных перед сериализацией.

        Проверяет, что товар активен и доступен в достаточном количестве.

        Args:
            attrs (dict): Данные для сериализации (например, quantity).

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если товар неактивен или недостаточно на складе.
        """
        quantity = attrs.get('quantity')
        instance = self.instance

        # Проверка для обновления существующего элемента
        if instance:
            product = instance.product
            if not product.is_active:
                raise serializers.ValidationError("Товар неактивен.")
            if quantity > product.stock:
                raise serializers.ValidationError("Недостаточно товара на складе.")

        return attrs
