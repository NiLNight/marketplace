"""
Middleware для безопасности и мониторинга.

Включает rate limiting, security headers, логирование и защиту от атак.
"""

import time
import logging
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

logger = logging.getLogger('security')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Добавляет security headers к ответам."""
    
    def process_response(self, request, response):
        """Добавляет security headers к ответу."""
        # Основные security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp
        
        # Strict Transport Security (только для HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware для защиты от DDoS атак."""
    
    def process_request(self, request):
        """Проверяет rate limits для запроса."""
        # Получаем IP адрес
        ip = self._get_client_ip(request)
        
        # Определяем тип запроса
        request_type = self._get_request_type(request)
        
        # Проверяем rate limit
        if not self._check_rate_limit(ip, request_type):
            logger.warning(f"Rate limit exceeded for IP: {ip}, type: {request_type}")
            return JsonResponse(
                {'detail': 'Too many requests', 'code': 'rate_limit_exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        return None
    
    def _get_client_ip(self, request):
        """Получает реальный IP адрес клиента."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_request_type(self, request):
        """Определяет тип запроса для rate limiting."""
        path = request.path.lower()
        
        if '/api/auth/login/' in path:
            return 'login'
        elif '/api/auth/register/' in path:
            return 'register'
        elif '/api/auth/verify/' in path:
            return 'verification_code'
        elif '/admin/' in path:
            return 'admin'
        elif '/api/' in path:
            return 'api'
        else:
            return 'general'
    
    def _check_rate_limit(self, ip, request_type):
        """Проверяет rate limit для IP и типа запроса."""
        # Получаем лимиты из настроек
        limits = getattr(settings, 'RATE_LIMITS', {
            'login': (5, 60),      # 5 запросов в минуту
            'register': (3, 3600),  # 3 запроса в час
            'verification_code': (5, 3600),  # 5 запросов в час
            'admin': (10, 60),      # 10 запросов в минуту
            'api': (100, 60),       # 100 запросов в минуту
            'general': (1000, 60),  # 1000 запросов в минуту
        })
        
        if request_type not in limits:
            return True
        
        max_requests, window = limits[request_type]
        cache_key = f"rate_limit:{ip}:{request_type}"
        
        # Получаем текущее количество запросов
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= max_requests:
            return False
        
        # Увеличиваем счетчик
        cache.set(cache_key, current_requests + 1, window)
        return True


class RequestLoggingMiddleware(MiddlewareMixin):
    """Логирует все запросы для мониторинга и безопасности."""
    
    def process_request(self, request):
        """Логирует входящий запрос."""
        request.start_time = time.time()
        
        # Логируем только важные запросы
        if self._should_log_request(request):
            logger.info(
                f"Request: {request.method} {request.path} "
                f"IP: {self._get_client_ip(request)} "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
            )
    
    def process_response(self, request, response):
        """Логирует ответ на запрос."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Логируем медленные запросы
            if duration > 1.0:  # Больше 1 секунды
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s IP: {self._get_client_ip(request)}"
                )
            
            # Логируем ошибки
            if response.status_code >= 400:
                logger.error(
                    f"Error response: {request.method} {request.path} "
                    f"status: {response.status_code} "
                    f"IP: {self._get_client_ip(request)}"
                )
        
        return response
    
    def _should_log_request(self, request):
        """Определяет, нужно ли логировать запрос."""
        # Не логируем статические файлы и health checks
        excluded_paths = [
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
        ]
        
        path = request.path.lower()
        return not any(excluded in path for excluded in excluded_paths)
    
    def _get_client_ip(self, request):
        """Получает реальный IP адрес клиента."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Базовая защита от SQL инъекций."""
    
    def process_request(self, request):
        """Проверяет запрос на подозрительные паттерны."""
        # Проверяем GET параметры
        for key, value in request.GET.items():
            if self._is_suspicious(value):
                logger.warning(
                    f"Potential SQL injection attempt in GET parameter '{key}': {value} "
                    f"IP: {self._get_client_ip(request)}"
                )
                return JsonResponse(
                    {'detail': 'Invalid request', 'code': 'security_violation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Проверяем POST данные
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self._is_suspicious(value):
                    logger.warning(
                        f"Potential SQL injection attempt in POST parameter '{key}': {value} "
                        f"IP: {self._get_client_ip(request)}"
                    )
                    return JsonResponse(
                        {'detail': 'Invalid request', 'code': 'security_violation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        return None
    
    def _is_suspicious(self, value):
        """Проверяет значение на подозрительные паттерны."""
        if not isinstance(value, str):
            return False
        
        suspicious_patterns = [
            'union select',
            'union all select',
            'drop table',
            'delete from',
            'insert into',
            'update set',
            'or 1=1',
            'or 1 = 1',
            '--',
            '/*',
            '*/',
            'xp_',
            'sp_',
            'exec ',
            'execute ',
        ]
        
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in suspicious_patterns)
    
    def _get_client_ip(self, request):
        """Получает реальный IP адрес клиента."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class HealthCheckMiddleware(MiddlewareMixin):
    """Middleware для health check endpoint."""
    
    def process_request(self, request):
        """Обрабатывает health check запросы."""
        if request.path == '/health/':
            return HttpResponse('OK', content_type='text/plain')
        return None 