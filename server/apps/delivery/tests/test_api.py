from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.delivery.models import City, PickupPoint
from unittest.mock import patch, MagicMock
from django.core.cache import cache

User = get_user_model()


def mock_get_pickup_points(request):
    """
    Мок-функция, которая имитирует DeliveryService.get_pickup_points.
    Она напрямую работает с БД, применяя фильтры и возвращая QuerySet,
    который затем будет пагинирован во View.
    """
    qs = PickupPoint.objects.filter(is_active=True).order_by('id')

    city_id = request.GET.get('city_id')
    if city_id:
        qs = qs.filter(city_id=city_id)

    query = request.GET.get('query') or request.GET.get('q')
    if query:
        qs = qs.filter(address__icontains=query)
    return qs


# Патчим метод СЕРВИСА, который вызывается из View
@patch('apps.delivery.services.delivery_services.DeliveryService.get_pickup_points', mock_get_pickup_points)
class DeliveryAPITest(TestCase):
    """
    Тесты для API: PickupPointListView и CityListView.
    """

    def setUp(self):
        cache.clear()  # Обязательно чистим кэш
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.city = City.objects.create(name='Москва')
        self.pickup1 = PickupPoint.objects.create(city=self.city, address='ул. Пушкина, д. 1', district='Центр')
        self.pickup2 = PickupPoint.objects.create(city=self.city, address='ул. Лермонтова, д. 2', district='Юг')

    def tearDown(self):
        cache.clear()  # И после теста

    def test_pickup_points_list(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_pickup_points_filter_by_city(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url, {'city_id': self.city.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Мок отфильтрует, и View отпагинирует результат (2 объекта)
        self.assertEqual(len(response.data['results']), 2)
        for item in response.data['results']:
            self.assertEqual(item['city']['id'], self.city.id)

    def test_pickup_points_search(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url, {'q': 'Пушкина'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['address'], 'ул. Пушкина, д. 1')

    # Отключаем основной мок для этого теста, чтобы проверить логику аутентификации
    @patch('apps.delivery.services.delivery_services.DeliveryService.get_pickup_points', new_callable=MagicMock)
    def test_pickup_points_unauthenticated(self, mock_get_points):
        self.client.force_authenticate(user=None)
        url = reverse('delivery:pickup_points')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_get_points.assert_not_called()

    def test_city_list(self):
        url = reverse('delivery:city_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_city_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('delivery:city_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pickup_points_pagination(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url, {'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('count', response.data)
        # С текущей логикой `count` будет равен 2, т.к. пагинатор видит 2 объекта от мока
        self.assertEqual(response.data['count'], 2)
        self.assertIn('next', response.data)
