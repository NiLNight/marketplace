import logging
from functools import wraps

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def handle_api_errors(view_func):
    """
    Декоратор для обработки ошибок в API-представлениях приложения orders.

    Обрабатывает общие и кастомные исключения, логирует ошибки и возвращает стандартизированные HTTP-ответы.

    Args:
        view_func: Функция представления, которую нужно обернуть.

    Returns:
        wrapper: Обернутая функция с обработкой ошибок.

    Raises:
        None: Декоратор перехватывает все исключения и возвращает HTTP-ответы.
    """

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        try:
            return view_func(self, request, *args, **kwargs)
        except KeyError as e:
            # Обрабатываем отсутствие ключей в запросе
            logger.warning(f"Missing key: {str(e)}, user={user_id}, path={request.path},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": f"{_('Отсутствует ключ')}: {str(e)}", "code": "missing_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            # Обрабатываем некорректные значения параметров
            logger.warning(f"Invalid value: {str(e)}, user={user_id}, "
                           f"path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": _("Некорректное значение параметра"), "code": "invalid_value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            # Обрабатываем ошибки валидации
            logger.warning(f"Validation error: {str(e)}, user={user_id}, path={request.path},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except APIException as e:
            # Обрабатываем API-исключения
            logger.warning(f"API error: {e.detail}, user={user_id}, path={request.path},"
                           f" IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except Exception as e:
            # Обрабатываем непредвиденные ошибки
            logger.error(f"Server error: {str(e)}, user={user_id}, path={request.path},"
                         f" IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": _("Внутренняя ошибка сервера"), "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper
