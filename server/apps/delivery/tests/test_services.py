from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch, MagicMock
from apps.delivery.models import City, PickupPoint
from apps.delivery.services.delivery_services import DeliveryService
from apps.delivery.services.query_services import PickupPointQueryService
from apps.delivery.exceptions import CityNotFound, ElasticsearchUnavailable
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class DeliveryServiceTest(TestCase):
    """
    Тесты для DeliveryService: get_pickup_points, get_cities, права, ошибки.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.city = City.objects.create(name='Москва')
        self.pickup = PickupPoint.objects.create(city=self.city, address='ул. Пушкина, д. 1')
        self.factory = RequestFactory()
        self.request = self.factory.get('/pickup_points/?city_id=%d' % self.city.id)
        self.request.user = self.user

    def test_get_pickup_points_authenticated(self):
        # пользователь по умолчанию аутентифицирован
        result = DeliveryService.get_pickup_points(self.request)
        self.assertIn(self.pickup, list(result))

    def test_get_pickup_points_unauthenticated(self):
        self.request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            DeliveryService.get_pickup_points(self.request)

    def test_get_cities_authenticated(self):
        # пользователь по умолчанию аутентифицирован
        result = DeliveryService.get_cities(self.request)
        self.assertIn(self.city, list(result))

    def test_get_cities_unauthenticated(self):
        self.request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            DeliveryService.get_cities(self.request)


class PickupPointQueryServiceTest(TestCase):
    """
    Тесты для PickupPointQueryService: поиск, фильтрация, ошибки, mock Elasticsearch.
    """

    def setUp(self):
        self.city = City.objects.create(name='Казань')
        self.pickup = PickupPoint.objects.create(city=self.city, address='ул. Баумана, д. 1', district='Центр')
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.request = self.factory.get('/pickup_points/?q=Баумана')
        self.request.user = self.user
        # пользователь по умолчанию аутентифицирован

    @patch('apps.delivery.services.query_services.PickupPointDocument')
    def test_search_pickup_points_elasticsearch(self, mock_doc):
        # Мокаем ответ Elasticsearch
        mock_search = MagicMock()
        mock_search.filter.return_value = mock_search
        mock_search.query.return_value = mock_search
        mock_search.sort.return_value = mock_search
        mock_search.__getitem__.return_value = mock_search
        mock_response = MagicMock()
        mock_response.__iter__.return_value = [MagicMock(id=self.pickup.id)]
        mock_response.hits.total.value = 1
        mock_search.execute.return_value = mock_response
        mock_doc.search.return_value = mock_search
        result = PickupPointQueryService.search_pickup_points(self.request)
        self.assertEqual(list(result)[0].id, self.pickup.id)

    def test_search_pickup_points_unauthenticated(self):
        self.request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            PickupPointQueryService.search_pickup_points(self.request)

    def test_search_pickup_points_invalid_city(self):
        request = self.factory.get('/pickup_points/?city_id=9999')
        request.user = self.user
        # пользователь по умолчанию аутентифицирован
        with self.assertRaises(CityNotFound):
            PickupPointQueryService.search_pickup_points(request)
