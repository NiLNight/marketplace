from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from apps.delivery.models import City, PickupPoint


class CityModelTest(TestCase):
    """
    Тесты для модели City: создание, валидация, уникальность, __str__.
    """

    def test_city_creation(self):
        city = City.objects.create(name='Москва')
        self.assertEqual(city.name, 'Москва')

    def test_city_str(self):
        city = City.objects.create(name='Санкт-Петербург')
        self.assertEqual(str(city), 'Санкт-Петербург')

    def test_city_empty_name(self):
        city = City(name='')
        with self.assertRaises(ValidationError):
            city.full_clean()

    def test_city_unique(self):
        City.objects.create(name='Казань')
        city2 = City(name='Казань')
        with self.assertRaises(ValidationError):
            city2.full_clean()
            city2.save()


class PickupPointModelTest(TestCase):
    """
    Тесты для модели PickupPoint: создание, валидация, уникальность, __str__, запрет смены is_active.
    """

    def setUp(self):
        self.city = City.objects.create(name='Москва')

    def test_pickup_point_creation(self):
        pp = PickupPoint.objects.create(city=self.city, address='ул. Пушкина, д. 1')
        self.assertEqual(pp.city, self.city)
        self.assertEqual(pp.address, 'ул. Пушкина, д. 1')

    def test_pickup_point_str(self):
        pp = PickupPoint.objects.create(city=self.city, address='ул. Лермонтова, д. 2')
        self.assertEqual(str(pp), f'{self.city.name}, ул. Лермонтова, д. 2')

    def test_pickup_point_empty_address(self):
        pp = PickupPoint(city=self.city, address='')
        with self.assertRaises(ValidationError):
            pp.full_clean()

    def test_pickup_point_unique(self):
        PickupPoint.objects.create(city=self.city, address='ул. Чехова, д. 3')
        pp2 = PickupPoint(city=self.city, address='ул. Чехова, д. 3')
        with self.assertRaises(ValidationError):
            pp2.full_clean()
            pp2.save()

    def test_pickup_point_forbid_is_active_change(self):
        pp = PickupPoint.objects.create(city=self.city, address='ул. Гоголя, д. 4')
        pp.is_active = False
        with self.assertRaises(ValidationError):
            pp.save()
