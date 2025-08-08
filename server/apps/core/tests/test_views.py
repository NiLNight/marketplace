"""
Тесты для views core приложения.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class HealthCheckViewTest(TestCase):
    """Тесты для health check view."""

    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint(self):
        """Проверяет, что health check endpoint возвращает корректный ответ."""
        url = reverse('core:health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'ok'})

    def test_health_check_anonymous_access(self):
        """Проверяет, что health check доступен анонимным пользователям."""
        url = reverse('core:health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK) 