from datetime import datetime
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import APIException
from functools import wraps
from apps.users.exceptions import UserServiceException, UserNotFound
import logging

logger = logging.getLogger(__name__)


def handle_user_api_errors(view_func):
    """Декоратор для обработки ошибок в представлениях пользователей.

    Логирует ошибки и преобразует исключения в стандартизированные ответы API.

    Args:
        view_func: Функция представления.

    Returns:
        Обернутая функция, которая обрабатывает ошибки.

    Raises:
        APIException: Для клиентских ошибок (400, 404 и т.д.).
        Exception: Для серверных ошибок (500).
    """

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        request = args[1]  # request всегда второй аргумент в APIView
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        try:
            return view_func(*args, **kwargs)
        except UserNotFound as e:
            logger.error(f"User not found: {str(e)}, user={user_id}, path={request.path}")
            raise APIException(detail=str(e), code=e.default_code)
        except UserServiceException as e:
            logger.error(f"User service error: {str(e)}, user={user_id}, path={request.path}")
            raise APIException(detail=str(e), code=e.default_code)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}, user={user_id}, path={request.path}")
            raise APIException(detail="Внутренняя ошибка сервера", code="internal_server_error")

    return wrapped_view


def set_jwt_cookies(response, user):
    """
    Устанавливает JWT-токены в cookies ответа.

    Args:
        response (HttpResponse): Объект ответа.
        user (User): Аутентифицированный пользователь.

    Returns:
        HttpResponse: Ответ с установленными cookies.
    """
    logger.debug(f"Setting JWT cookies for user {user.id}")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    cookie_params = {
        'domain': settings.SIMPLE_JWT.get('AUTH_COOKIE_DOMAIN'),
        'path': settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/'),
        'secure': settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
        'httponly': settings.SIMPLE_JWT.get('AUTH_COOKIE_HTTP_ONLY', True),
        'samesite': settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax'),
    }

    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=access_token,
        expires=datetime.utcnow() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
        **cookie_params
    )

    response.set_cookie(
        key=settings.SIMPLE_JWT['REFRESH_COOKIE'],
        value=refresh_token,
        expires=datetime.utcnow() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
        **cookie_params
    )

    logger.info(f"JWT cookies set successfully for user {user.id}")
    return response
