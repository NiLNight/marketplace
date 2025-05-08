import logging
from datetime import datetime
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException, PermissionDenied
from apps.users.exceptions import UserException

logger = logging.getLogger(__name__)


def set_jwt_cookies(response, user):
    """Устанавливает JWT-токены в cookies ответа.

    Args:
        response (HttpResponse): Объект ответа.
        user (User): Аутентифицированный пользователь.

    Returns:
        HttpResponse: Ответ с установленными cookies.
    """
    refresh = RefreshToken.for_user(user)
    refresh.set_jti()  # Ротация токена
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    cookie_params = {
        'domain': settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN', None),
        'path': settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        'secure': settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', True),
        'httponly': settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
        'samesite': settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Strict'),
    }

    access_expires = datetime.utcnow() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    refresh_expires = datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    if access_expires < datetime.utcnow() or refresh_expires < datetime.utcnow():
        raise ValueError("Invalid token lifetime")

    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=access_token,
        expires=access_expires,
        **cookie_params
    )

    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value=refresh_token,
        expires=refresh_expires,
        **cookie_params
    )

    logger.info(f"JWT cookies set for user={user.id}")
    return response


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях приложения users.

    Логирует ошибки и возвращает стандартизированные HTTP-ответы.

    Args:
        view_func: Функция представления для обертки.

    Returns:
        Обернутая функция с обработкой ошибок.
    """

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        try:
            return view_func(self, request, *args, **kwargs)
        except KeyError as e:
            logger.warning(f"Missing key: {str(e)}, user={user_id}, path={path}")
            return Response(
                {"error": f"Отсутствует ключ: {str(e)}", "code": "missing_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (ValidationError, ValueError) as e:
            logger.warning(f"Invalid data: {str(e)}, user={user_id}, path={path}")
            return Response(
                {"error": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {str(e)}, user={user_id}, path={path}")
            return Response(
                {"error": str(e), "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        except UserException as e:
            logger.warning(f"User error: {e.detail}, user={user_id}, path={path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except APIException as e:
            logger.warning(f"API error: {e.detail}, user={user_id}, path={path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Server error: {str(e)}, user={user_id}, path={path}")
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper
