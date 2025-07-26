from datetime import datetime
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def get_cookie_params():
    """Возвращает стандартизированный словарь параметров для cookie."""
    return {
        'domain': settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN'),
        'path': settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        'secure': settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', not settings.DEBUG),
        'httponly': settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
        'samesite': settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
    }


def set_jwt_cookies(response, user):
    """Устанавливает JWT-токены в cookies ответа.

    Создает новые access и refresh токены для пользователя и устанавливает их в cookies
    с учетом настроек безопасности из конфигурации.

    Args:
        response (HttpResponse): Объект ответа.
        user (User): Аутентифицированный пользователь.

    Returns:
        HttpResponse: Ответ с установленными cookies.

    Raises:
        ValueError: Если срок действия токена некорректен.
    """
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    access_expires = datetime.utcnow() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    refresh_expires = datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

    params = get_cookie_params()

    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=access_token,
        expires=access_expires,
        **params
    )
    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value=refresh_token,
        expires=refresh_expires,
        **params
    )
    return response


def delete_jwt_cookies(response):
    """Удаляет JWT-токены из httpOnly cookies."""
    params = get_cookie_params()

    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=params['path'],
        domain=params['domain'],
        samesite=params['samesite']
    )
    response.delete_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        path=params['path'],
        domain=params['domain'],
        samesite=params['samesite']
    )
    return response