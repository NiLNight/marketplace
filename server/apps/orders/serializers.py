from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.orders.models import Order
from apps.carts.serializers import CartItemSerializer
from apps.delivery.serializers import DeliverySerializer, PickupPointSerializer


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка заказов.

    Преобразует объекты Order в JSON, включая основные поля заказа для отображения в списке.
    Проверяет корректность статуса, общей стоимости и выбора доставки/пункта выдачи.
    """
    delivery = DeliverySerializer(read_only=True)
    pickup_point = PickupPointSerializer(read_only=True)

    class Meta:
        """Метаданные сериализатора OrderSerializer."""
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'delivery', 'pickup_point']

    def validate(self, attrs):
        """
        Проверяет корректность данных перед сериализацией.

        Убеждается, что статус валиден, total_price неотрицателен, и указан либо delivery, либо pickup_point.

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
                raise serializers.ValidationError({"status": _("Недопустимый статус заказа")})
            if instance.total_price < 0:
                raise serializers.ValidationError({"total_price": _("Общая стоимость не может быть отрицательной")})
            if instance.delivery and instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": _("Нельзя указать и доставку, и пункт выдачи одновременно")}
                )
            if not instance.delivery and not instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": _("Необходимо указать либо доставку, либо пункт выдачи")}
                )
        return attrs


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального отображения заказа.

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

    def validate(self, attrs):
        """
        Проверяет корректность данных перед сериализацией.

        Убеждается, что статус валиден, total_price неотрицателен, delivery/pickup_point активны,
        и все товары активны.

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
                raise serializers.ValidationError({"status": _("Недопустимый статус заказа")})
            if instance.total_price < 0:
                raise serializers.ValidationError({"total_price": _("Общая стоимость не может быть отрицательной")})
            if not instance.delivery and not instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": _("Необходимо указать либо доставку, либо пункт выдачи")}
                )
            if instance.delivery and instance.pickup_point:
                raise serializers.ValidationError(
                    {"delivery": _("Нельзя указать и доставку, и пункт выдачи одновременно")}
                )
            if instance.pickup_point and not instance.pickup_point.is_active:
                raise serializers.ValidationError({"pickup_point": _("Пункт выдачи неактивен")})
            for item in instance.order_items.all():
                if not item.product.is_active:
                    raise serializers.ValidationError(
                        {"items": _("Товар {item.product.title} неактивен")}
                    )
        return attrs
