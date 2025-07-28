"""
Middleware для безопасности и мониторинга.
"""
import time
import logging

from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')  # Отдельный логгер для безопасности


# --- Утилита для получения IP, чтобы не дублировать код ---
def get_client_ip(request):
    """Получает реальный IP адрес клиента."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Добавляет правильные security headers к ответам."""

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'

        csp_parts = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            "img-src": ["'self'", "data:", "http://localhost:8000", "https://*.yourdomain.com"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "frame-ancestors": ["'none'"],
        }

        # В режиме DEBUG разрешаем 'unsafe-eval' для работы некоторых dev-инструментов
        if settings.DEBUG:
            csp_parts["script-src"].append("'unsafe-eval'")

        csp_policy = "; ".join([f"{key} {' '.join(values)}" for key, values in csp_parts.items()])
        response['Content-Security-Policy'] = csp_policy

        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Простой middleware для ограничения частоты запросов.
    Примечание: Встроенный throttling в DRF является более гибким решением.
    """

    def process_request(self, request):
        ip = get_client_ip(request)
        cache_key = f"rate_limit:{ip}"

        # Простой лимит: не более 100 запросов за 10 секунд
        limit = 100
        timeout = 10

        count = cache.get(cache_key, 0)
        if count >= limit:
            security_logger.warning(f"Rate limit exceeded for IP: {ip}")
            return JsonResponse(
                {'detail': 'Too many requests', 'code': 'rate_limit_exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Если это первый запрос, устанавливаем ключ с таймаутом
        if count == 0:
            cache.set(cache_key, 1, timeout=timeout)
        else:
            # Иначе просто инкрементируем
            cache.incr(cache_key)

        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """Логирует информацию о запросах."""

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            # Логируем только медленные запросы и ошибки
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {duration:.2f}s for {request.method} {request.path} from IP: {get_client_ip(request)}")

            if 400 <= response.status_code < 600:
                user_info = request.user.username if request.user.is_authenticated else 'Anonymous'
                logger.error(
                    f"Error response: {response.status_code} for {request.method} {request.path} "
                    f"from IP: {get_client_ip(request)}, User: {user_info}"
                )
        return response


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Базовая защита от очевидных SQL-инъекций."""
    suspicious_patterns = [
        'union', 'select', 'drop', 'insert', 'update', 'delete',
        '1=1', 'or --', 'or 1>0', 'or 1<0',
        '--', '/*', '*/', 'xp_', 'sp_'
    ]

    def process_request(self, request):
        for key, values in request.GET.lists():
            for value in values:
                if self._is_suspicious(value):
                    security_logger.critical(
                        f"Potential SQL injection detected in GET param '{key}' from IP: {get_client_ip(request)}. Value: {value}")
                    return JsonResponse({'detail': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
        return None

    def _is_suspicious(self, value):
        if not isinstance(value, str):
            return False
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in self.suspicious_patterns)


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health/':
            logger.info("Health check endpoint was hit! Responding OK.")
            return JsonResponse({'status': 'ok'})

        response = self.get_response(request)

        return response
