from rest_framework import serializers
from django.core.exceptions import ValidationError
from apps.delivery.models import City, Delivery, PickupPoint


class CitySerializer(serializers.ModelSerializer):
    """Сериализатор для городов.

    Преобразует объекты City в JSON, включая название города.
    """

    class Meta:
        """Метаданные сериализатора CitySerializer."""
        model = City
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']


class DeliverySerializer(serializers.ModelSerializer):
    """Сериализатор для адресов доставки.

    Преобразует объекты Delivery в JSON, включая адрес и стоимость доставки.
    """

    class Meta:
        """Метаданные сериализатора DeliverySerializer."""
        model = Delivery
        fields = ['id', 'address', 'cost', 'is_primary']
        read_only_fields = ['id', 'address', 'cost', 'is_primary']

    def validate(self, attrs):
        """Проверяет корректность данных перед сериализацией.

        Проверяет, что стоимость доставки неотрицательна.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        instance = self.instance
        if instance and instance.cost < 0:
            raise serializers.ValidationError({"cost": "Стоимость доставки не может быть отрицательной."})
        return attrs


class PickupPointSerializer(serializers.ModelSerializer):
    """Сериализатор для пунктов выдачи.

    Преобразует объекты PickupPoint в JSON, включая город и адрес.
    Используется для отображения списка пунктов выдачи и выбора при создании заказа.
    """
    city = CitySerializer(read_only=True)

    class Meta:
        """Метаданные сериализатора PickupPointSerializer."""
        model = PickupPoint
        fields = ['id', 'city', 'address', 'is_active']
        read_only_fields = ['id', 'city', 'address', 'is_active']

    def validate(self, attrs):
        """Проверяет корректность данных перед сериализацией.

        Проверяет, что пункт выдачи активен.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если пункт выдачи неактивен.
        """
        instance = self.instance
        if instance and not instance.is_active:
            raise serializers.ValidationError({"is_active": "Пункт выдачи неактивен."})
        return attrs
