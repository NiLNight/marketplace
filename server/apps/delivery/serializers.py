from rest_framework import serializers
from apps.delivery.models import City, PickupPoint


class CitySerializer(serializers.ModelSerializer):
    """
    Сериализатор для городов.
    """

    class Meta:
        model = City
        fields = ['id', 'name']


class PickupPointSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пунктов выдачи.
    """
    city = CitySerializer(read_only=True)

    class Meta:
        model = PickupPoint
        fields = ['id', 'city', 'address', 'district', 'is_active']
