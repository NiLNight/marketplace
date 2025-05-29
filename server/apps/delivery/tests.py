"""Модуль тестов для приложения delivery.

Содержит тесты для проверки функциональности пунктов выдачи,
поиска, фильтрации и других возможностей приложения delivery.
"""

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from apps.delivery.models import City, PickupPoint
from apps.delivery.services.delivery_services import DeliveryService
from apps.delivery.exceptions import CityNotFound, ElasticsearchUnavailable


class CityTests(TestCase):
    """Тесты для модели City.

    Проверяет создание, валидацию и получение городов.

    Attributes:
        client (Client): Тестовый клиент Django.
        cities_url (str): URL для работы с городами.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.cities_url = reverse('delivery:city_list')
        self.city = City.objects.create(name='Москва')

    def test_city_creation(self):
        """Тест создания города."""
        city = City.objects.create(name='Санкт-Петербург')
        self.assertEqual(city.name, 'Санкт-Петербург')

    def test_city_str(self):
        """Тест строкового представления города."""
        self.assertEqual(str(self.city), 'Москва')


class PickupPointTests(TestCase):
    """Тесты для модели PickupPoint.

    Проверяет создание, валидацию, поиск и фильтрацию пунктов выдачи.

    Attributes:
        client (Client): Тестовый клиент Django.
        pickup_points_url (str): URL для работы с пунктами выдачи.
    """

    def setUp(self):
        """Инициализация данных для тестов."""
        self.client = Client()
        self.pickup_points_url = reverse('delivery:pickup_point_list')
        self.city = City.objects.create(name='Москва')
        self.pickup_point = PickupPoint.objects.create(
            city=self.city,
            address='ул. Пушкина, д. 1',
            district='Центральный'
        )

    def test_pickup_point_creation(self):
        """Тест создания пункта выдачи."""
        pickup_point = PickupPoint.objects.create(
            city=self.city,
            address='ул. Лермонтова, д. 2',
            district='Южный'
        )
        self.assertEqual(pickup_point.address, 'ул. Лермонтова, д. 2')
        self.assertEqual(pickup_point.city, self.city)

    def test_pickup_point_str(self):
        """Тест строкового представления пункта выдачи."""
        expected = f"{self.city.name}, {self.pickup_point.address}"
        self.assertEqual(str(self.pickup_point), expected)

    def test_pickup_point_search(self):
        """Тест поиска пунктов выдачи."""
        # Создаем тестовые данные
        PickupPoint.objects.create(
            city=self.city,
            address='ул. Гоголя, д. 3',
            district='Северный'
        )
        # Проверяем поиск по адресу
        response = self.client.get(f"{self.pickup_points_url}?q=Гоголя")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем поиск по району
        response = self.client.get(f"{self.pickup_points_url}?district=Северный")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
