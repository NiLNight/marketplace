"""
Middleware для безопасности.
"""
import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


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
