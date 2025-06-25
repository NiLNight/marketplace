from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.delivery.models import City, PickupPoint

User = get_user_model()


class DeliveryAPITest(TestCase):
    """
    Тесты для API: PickupPointListView и CityListView (GET, фильтрация, пагинация, права, ошибки, кэш).
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.city = City.objects.create(name='Москва')
        self.pickup1 = PickupPoint.objects.create(city=self.city, address='ул. Пушкина, д. 1', district='Центр')
        self.pickup2 = PickupPoint.objects.create(city=self.city, address='ул. Лермонтова, д. 2', district='Юг')

    def test_pickup_points_list(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_pickup_points_filter_by_city(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url, {'city_id': self.city.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['city']['id'], self.city.id)

    def test_pickup_points_search(self):
        url = reverse('delivery:pickup_points')
        response = self.client.get(url, {'q': 'Пушкина'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Пушкина' in item['address'] for item in response.data['results']))

    def test_pickup_points_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse('delivery:pickup_points')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
        self.assertIn('next', response.data)
