"""
Тесты для middleware.
"""
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from apps.core.middleware import SecurityHeadersMiddleware, get_client_ip


class SecurityHeadersMiddlewareTest(TestCase):
    """Тесты для SecurityHeadersMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware()

    def test_security_headers_added(self):
        """Проверяет, что security headers добавляются к ответу."""
        request = self.factory.get('/')
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        # Проверяем наличие security headers
        self.assertIn('X-Content-Type-Options', processed_response)
        self.assertEqual(processed_response['X-Content-Type-Options'], 'nosniff')
        
        self.assertIn('X-Frame-Options', processed_response)
        self.assertEqual(processed_response['X-Frame-Options'], 'DENY')
        
        self.assertIn('Content-Security-Policy', processed_response)

    def test_https_headers(self):
        """Проверяет, что HSTS header добавляется для HTTPS запросов."""
        request = self.factory.get('/', **{'wsgi.url_scheme': 'https'})
        response = HttpResponse()
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Strict-Transport-Security', processed_response)


class GetClientIPTest(TestCase):
    """Тесты для функции get_client_ip."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_client_ip_from_x_forwarded_for(self):
        """Проверяет получение IP из X-Forwarded-For header."""
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_get_client_ip_from_remote_addr(self):
        """Проверяет получение IP из REMOTE_ADDR."""
        request = self.factory.get('/', REMOTE_ADDR='127.0.0.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1') 