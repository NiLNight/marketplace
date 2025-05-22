from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.orders.models import Order
from apps.carts.serializers import CartItemSerializer
from apps.delivery.serializers import PickupPointSerializer


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка заказов.

    Преобразует объекты Order в JSON, включая основные поля заказа для отображения в списке.
    Проверяет корректность статуса, общей стоимости и пункта выдачи.
    """
    pickup_point = PickupPointSerializer(read_only=True)

    class Meta:
        """Метаданные сериализатора OrderSerializer."""
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'pickup_point']

    def validate(self, attrs):
        """
        Проверяет корректность данных перед сериализацией.

        Убеждается, что статус валиден, total_price неотрицателен, и указан активный pickup_point.

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
            if not instance.pickup_point:
                raise serializers.ValidationError({"pickup_point": _("Пункт выдачи обязателен")})
            if not instance.pickup_point.is_active:
                raise serializers.ValidationError({"pickup_point": _("Пункт выдачи неактивен!")})
        return attrs


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального отображения заказа.

    Преобразует объекты Order в JSON, включая элементы заказа и пункт выдачи.
    Проверяет корректность статуса, общей стоимости и связанных данных.
    """
    items = CartItemSerializer(
        many=True,
        source='order_items',
        read_only=True,
        help_text='Список элементов заказа из корзины.'
    )
    pickup_point = PickupPointSerializer(read_only=True)

    class Meta:
        """Метаданные сериализатора OrderDetailSerializer."""
        model = Order
        fields = ['id', 'status', 'total_price', 'created', 'items', 'pickup_point']

    def validate(self, attrs):
        """
        Проверяет корректность данных перед сериализацией.

        Убеждается, что статус валиден, total_price неотрицателен, pickup_point активен,
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
            if not instance.pickup_point:
                raise serializers.ValidationError({"pickup_point": _("Пункт выдачи обязателен!")})
            if not instance.pickup_point.is_active:
                raise serializers.ValidationError({"pickup_point": _("Пункт выдачи неактивен")})
            for item in instance.order_items.all():
                if not item.product.is_active:
                    raise serializers.ValidationError(
                        {"items": _("Товар {item.product.title} неактивен")}
                    )
        return attrs
