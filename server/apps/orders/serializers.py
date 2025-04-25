from rest_framework import serializers
from apps.orders.models import Order
from apps.carts.serializers import CartItemSerializer


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для списка заказов.

    Преобразует объекты Order в JSON, включая основные поля заказа для отображения в списке.
    Проверяет корректность статуса и общей стоимости заказа.
    """

    class Meta:
        """Метаданные сериализатора OrderSerializer.

        Определяет модель и сериализуемые поля.
        """
        model = Order
        fields = ['id', 'status', 'total_price', 'created']
        read_only_fields = ['id', 'status', 'total_price', 'created']

    def validate(self, attrs):
        """Проверка корректности данных перед сериализацией.

        Проверяет, что статус заказа валиден и общая стоимость неотрицательна.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если статус недопустим или общая стоимость некорректна.
        """
        instance = self.instance
        if instance:
            if instance.status not in dict(Order.STATUS_CHOICES):
                raise serializers.ValidationError({"status": "Недопустимый статус заказа."})
            if instance.total_price < 0:
                raise serializers.ValidationError({"total_price": "Общая стоимость не может быть отрицательной."})
        return attrs


class OrderDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения заказа.

    Преобразует объекты Order в JSON, включая элементы заказа и информацию о доставке.
    Проверяет корректность статуса, общей стоимости и связанных данных.
    """
    items = CartItemSerializer(
        many=True,
        source='order_items',
        read_only=True,
        help_text='Список элементов заказа из корзины.'
    )

    class Meta:
        """Метаданные сериализатора OrderDetailSerializer.

        Определяет модель и сериализуемые поля.
        """
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'items', 'delivery']
        read_only_fields = ['id', 'status', 'total_price', 'created', 'items', 'delivery']

    def validate(self, attrs):
        """Проверка корректности данных перед сериализацией.

        Проверяет, что статус заказа валиден, общая стоимость неотрицательна,
        доставка существует и все товары активны.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        instance = self.instance
        if instance:
            # Проверка статуса
            if instance.status not in dict(Order.STATUS_CHOICES):
                raise serializers.ValidationError({"status": "Недопустимый статус заказа."})

            # Проверка общей стоимости
            if instance.total_price < 0:
                raise serializers.ValidationError({"total_price": "Общая стоимость не может быть отрицательной."})

            # Проверка доставки
            if not instance.delivery:
                raise serializers.ValidationError({"delivery": "Доставка не указана."})

            # Проверка активности товаров в order_items
            for item in instance.order_items.all():
                if not item.product.is_active:
                    raise serializers.ValidationError(
                        {"items": f"Товар {item.product.title} неактивен."}
                    )

        return attrs
