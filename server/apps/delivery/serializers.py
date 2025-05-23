from rest_framework import serializers
from apps.delivery.models import City, PickupPoint
from django.utils.translation import gettext_lazy as _


class SearchSerializer(serializers.Serializer):
    """
    Сериализатор для валидации поисковых запросов.

    Проверяет корректность параметров поиска, таких как запрос пользователя.
    """
    query = serializers.CharField(max_length=255, required=False)

    def validate_query(self, value):
        """
        Проверяет, что поисковый запрос не пустой.

        Args:
            value (str): Значение поискового запроса.

        Returns:
            str: Валидированное значение.

        Raises:
            ValidationError: Если запрос пустой или содержит только пробелы.
        """
        if value and not value.strip():
            raise serializers.ValidationError(_("Поисковый запрос не может быть пустым."))
        return value


class CitySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели City.

    Используется для сериализации данных о городах.
    """

    class Meta:
        model = City
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']


class PickupPointSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели PickupPoint.

    Используется для сериализации данных о пунктах выдачи, включая связанный город.
    """
    city = CitySerializer(read_only=True)

    class Meta:
        model = PickupPoint
        fields = ['id', 'city', 'address', 'district', 'is_active']
        read_only_fields = ['id', 'city', 'address', 'district', 'is_active']
