import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException
from apps.carts.exceptions import CartException

logger = logging.getLogger(__name__)


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях приложения carts.

    Обрабатывает общие и кастомные исключения, логирует ошибки и возвращает стандартизированные HTTP-ответы.

    Args:
        view_func: Функция представления, которую нужно обернуть.

    Returns:
        wrapper: Обернутая функция с обработкой ошибок.
    """

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        try:
            return view_func(self, request, *args, **kwargs)
        except KeyError as e:
            logger.warning(f"Missing key: {str(e)}, user={user_id}")
            return Response(
                {"error": f"Отсутствует ключ: {str(e)}", "code": "missing_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (ValidationError, ValueError) as e:
            logger.warning(f"Invalid data: {str(e)}, user={user_id}")
            return Response(
                {"error": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CartException as e:
            logger.warning(f"Cart error: {e.detail}, user={user_id}")
            return Response(
                {"error": e.detail, "code": e.__class__.__name__.lower()},
                status=e.status_code
            )
        except APIException as e:
            logger.warning(f"API error: {e.detail}, user={user_id}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Server error: {str(e)}, user={user_id}")
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper
