from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.delivery.models import City, Delivery, PickupPoint


class CitySerializer(serializers.ModelSerializer):
    """
    Сериализатор для городов.

    Преобразует объекты City в JSON, включая название города.
    """

    class Meta:
        """Метаданные сериализатора CitySerializer."""
        model = City
        fields = ['id', 'name']


class DeliverySerializer(serializers.ModelSerializer):
    """
    Сериализатор для адресов доставки.

    Преобразует объекты Delivery в JSON, включая адрес и стоимость доставки.
    Проверяет корректность адреса и стоимости.
    """

    class Meta:
        """Метаданные сериализатора DeliverySerializer."""
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

        Проверяет, что стоимость доставки неотрицательна.

        Args:
            attrs (dict): Данные для сериализации.

        Returns:
            dict: Валидированные данные.

        Raises:
            serializers.ValidationError: Если данные некорректны.
        """
        if attrs.get('cost', 0) < 0:
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
        """Метаданные сериализатора PickupPointSerializer."""
        model = PickupPoint
        fields = ['id', 'city', 'address', 'is_active']

    def validate_address(self, value):
        """
        Проверяет, что адрес содержит не менее 5 символов.

        Args:
            value (str): Значение поля address.

        Returns:
            str: Валидированное значение.

        Raises:
            serializers.ValidationError: Если адрес слишком короткий.
        """
        if len(value.strip()) < 5:
            raise serializers.ValidationError(_("Адрес должен содержать не менее 5 символов"))
        return value

    def validate(self, attrs):
        """
        Проверяет корректность данных перед сериализацией.

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
            raise serializers.ValidationError({"is_active": _("Пункт выдачи неактивен")})
        return attrs
