from django.test import TestCase
from apps.delivery.models import City, PickupPoint
from apps.delivery.serializers import SearchSerializer, CitySerializer, PickupPointSerializer


class SearchSerializerTest(TestCase):
    """
    Тесты для SearchSerializer: валидация поискового запроса.
    """

    def test_valid_query(self):
        data = {'query': 'Москва'}
        serializer = SearchSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_query(self):
        data = {'query': ''}
        serializer = SearchSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('query', serializer.errors)

    def test_no_query_field(self):
        data = {}
        serializer = SearchSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_whitespace_query(self):
        data = {'query': '   '}
        serializer = SearchSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('query', serializer.errors)


class CitySerializerTest(TestCase):
    """
    Тесты для CitySerializer: сериализация города.
    """

    def test_city_serializer(self):
        city = City.objects.create(name='Казань')
        serializer = CitySerializer(instance=city)
        self.assertEqual(serializer.data['id'], city.id)
        self.assertEqual(serializer.data['name'], 'Казань')


class PickupPointSerializerTest(TestCase):
    """
    Тесты для PickupPointSerializer: сериализация пункта выдачи.
    """

    def setUp(self):
        self.city = City.objects.create(name='Казань')
        self.pickup_point = PickupPoint.objects.create(city=self.city, address='ул. Баумана, д. 1', district='Центр')

    def test_pickup_point_serializer(self):
        serializer = PickupPointSerializer(instance=self.pickup_point)
        self.assertEqual(serializer.data['id'], self.pickup_point.id)
        self.assertEqual(serializer.data['address'], 'ул. Баумана, д. 1')
        self.assertEqual(serializer.data['district'], 'Центр')
        self.assertEqual(serializer.data['is_active'], True)
        self.assertEqual(serializer.data['city']['id'], self.city.id)
        self.assertEqual(serializer.data['city']['name'], self.city.name)
