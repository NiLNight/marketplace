from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.delivery.models import City, Delivery, PickupPoint


class CitySerializer(serializers.ModelSerializer):
    """
    Сериализатор для городов.

    Преобразует объекты City в JSON, включая название города.
    """

    class Meta:
        model = City
        fields = ['id', 'name']


class DeliverySerializer(serializers.ModelSerializer):
    """
    Сериализатор для адресов доставки.

    Преобразует объекты Delivery в JSON, включая адрес и стоимость доставки.
    Проверяет корректность адреса и стоимости.
    """

    class Meta:
        model = Delivery
        fields = ['id', 'address', 'cost', 'is_primary']

    def validate_address(self, value):
        """
        Проверяет, что адрес не пустой.

        Args:
            value (str): Значение поля address.

        Returns:
            str: Валидированное значение.

        Raises:
            serializers.ValidationError: Если адрес пустой.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(_("Адрес не может быть пустым"))
        return value

    def validate(self, attrs):
        """
        Проверяет корректность данных перед сериализацией.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        cost = attrs.get('cost')
        if cost is not None and cost < 0:
            raise serializers.ValidationError({"cost": _("Стоимость доставки не может быть отрицательной")})
        return attrs


class PickupPointSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пунктов выдачи.

    Преобразует объекты PickupPoint в JSON, включая город и адрес.
    Используется только для чтения, обновление пунктов выдачи не поддерживается.
    """
    city = CitySerializer(read_only=True)

    class Meta:
        model = PickupPoint
        fields = ['id', 'city', 'address', 'is_active']
