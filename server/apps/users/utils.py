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


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях приложения users.

    Логирует ошибки и возвращает стандартизированные HTTP-ответы.
    Обрабатывает различные типы исключений и преобразует их в соответствующие HTTP-ответы.

    Args:
        view_func (callable): Функция представления для обертки.

    Returns:
        callable: Обернутая функция с обработкой ошибок.

    Raises:
        Response: HTTP-ответ с соответствующим статусом и описанием ошибки.
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
