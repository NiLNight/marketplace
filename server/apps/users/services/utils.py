"""
Утилиты для работы с JWT:
- Установка токенов в cookies
- Настройки безопасности
"""
from datetime import datetime
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookies(response, user):
    """
    Устанавливает JWT-токены в cookies ответа
    Args:
        response (HttpResponse): Объект ответа
        user (user): Аутентифицированный пользователь
    Returns:
        HttpResponse: Ответ с установленными cookies
    """
    # Генерация токенов
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Базовые параметры cookies
    cookie_params = {
        'domain': settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN'),
        'path': settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        'secure': settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        'httponly': settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
        'samesite': settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),
    }

    # Установка access token
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=access_token,
        expires=datetime.utcnow() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        **cookie_params
    )

    # Установка refresh token
    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value=refresh_token,
        expires=datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        **cookie_params
    )

    return response
