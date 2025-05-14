import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException
from apps.delivery.exceptions import DeliveryNotFound, PickupPointNotFound, CityNotFound

logger = logging.getLogger(__name__)


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях приложения delivery.

    Обрабатывает стандартные и кастомные исключения, логирует ошибки и возвращает стандартизированные HTTP-ответы.

    Args:
        view_func: Функция представления, которую нужно обернуть.

    Returns:
        callable: Обернутая функция с обработкой ошибок.
    """

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        try:
            return view_func(self, request, *args, **kwargs)
        except KeyError as e:
            logger.warning(
                f"Missing key: {str(e)}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": f"Отсутствует ключ: {str(e)}", "code": "missing_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            logger.warning(
                f"Validation error: {str(e)}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DeliveryNotFound as e:
            logger.warning(
                f"Delivery not found: {e.detail}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except PickupPointNotFound as e:
            logger.warning(
                f"Pickup point not found: {e.detail}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except CityNotFound as e:
            logger.warning(
                f"City not found: {e.detail}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except APIException as e:
            logger.warning(
                f"API error: {e.detail}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except Exception as e:
            logger.error(
                f"Server error: {str(e)}, user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper
