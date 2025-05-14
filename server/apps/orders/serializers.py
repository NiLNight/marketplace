from rest_framework import serializers
from django.core.exceptions import ValidationError
from apps.orders.models import Order
from apps.carts.serializers import CartItemSerializer
from apps.delivery.serializers import DeliverySerializer, PickupPointSerializer


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для списка заказов.

    Преобразует объекты Order в JSON, включая основные поля заказа для отображения в списке.
    Проверяет корректность статуса, общей стоимости и выбора доставки/пункта выдачи.
    """
    delivery = DeliverySerializer(read_only=True)
    pickup_point = PickupPointSerializer(read_only=True)

    class Meta:
        """Метаданные сериализатора OrderSerializer."""
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'delivery', 'pickup_point']
        read_only_fields = ['id', 'status', 'total_price', 'created', 'delivery', 'pickup_point']

    def validate(self, attrs):
        """Проверяет корректность данных перед сериализацией.

        Проверяет, что статус заказа валиден, общая стоимость неотрицательна,
        и указан либо адрес доставки, либо пункт выдачи.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        instance = self.instance
        if instance:
            if instance.status not in dict(Order.STATUS_CHOICES):
                raise serializers.ValidationError({"status": "Недопустимый статус заказа."})
            if instance.total_price < 0:
                raise serializers.ValidationError({"total_price": "Общая стоимость не может быть отрицательной."})
            if instance.delivery and instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": "Нельзя указать и доставку, и пункт выдачи одновременно."}
                )
            if not instance.delivery and not instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": "Необходимо указать либо доставку, либо пункт выдачи."}
                )
        return attrs


class OrderDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения заказа.

    Преобразует объекты Order в JSON, включая элементы заказа, доставку и пункт выдачи.
    Проверяет корректность статуса, общей стоимости и связанных данных.
    """
    items = CartItemSerializer(
        many=True,
        source='order_items',
        read_only=True,
        help_text='Список элементов заказа из корзины.'
    )
    delivery = DeliverySerializer(read_only=True)
    pickup_point = PickupPointSerializer(read_only=True)

    class Meta:
        """Метаданные сериализатора OrderDetailSerializer."""
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'items', 'delivery', 'pickup_point']
        read_only_fields = ['id', 'status', 'total_price', 'created', 'items', 'delivery', 'pickup_point']

    def validate(self, attrs):
        """Проверяет корректность данных перед сериализацией.

        Проверяет, что статус заказа валиден, общая стоимость неотрицательна,
        доставка или пункт выдачи существуют, и все товары активны.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        instance = self.instance
        if instance:
            if instance.status not in dict(Order.STATUS_CHOICES):
                raise serializers.ValidationError({"status": "Недопустимый статус заказа."})
            if instance.total_price < 0:
                raise serializers.ValidationError({"total_price": "Общая стоимость не может быть отрицательной."})
            if instance.delivery and instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": "Нельзя указать и доставку, и пункт выдачи одновременно."}
                )
            if not instance.delivery and not instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": "Необходимо указать либо доставку, либо пункт выдачи."}
                )
            if instance.pickup_point and not instance.pickup_point.is_active:
                raise serializers.ValidationError({"pickup_point": "Пункт выдачи неактивен."})
            for item in instance.order_items.all():
                if not item.product.is_active:
                    raise serializers.ValidationError(
                        {"items": f"Товар {item.product.title} неактивен."}
                    )
        return attrs
