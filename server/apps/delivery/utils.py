import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException, PermissionDenied
from apps.delivery.exceptions import CityNotFound, PickupPointNotFound, ElasticsearchUnavailable
from typing import Dict, Any
from django.http import HttpRequest

logger = logging.getLogger(__name__)


def get_filter_params(request: HttpRequest) -> Dict[str, Any]:
    """Извлекает параметры фильтрации из HTTP-запроса."""
    params = request.GET
    result = {
        'city_id': None,
        'district': None,
    }
    try:
        city_id = params.get('city_id')
        if city_id is not None:
            result['city_id'] = int(city_id)
        result['district'] = params.get('district')
        return result
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid filter parameters: {str(e)}")
        raise CityNotFound(f"Некорректные параметры фильтрации: {str(e)}")


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях приложения delivery."""

    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        try:
            return view_func(self, request, *args, **kwargs)
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": str(e), "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        except KeyError as e:
            logger.warning(f"Missing key: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": f"Отсутствует ключ: {str(e)}", "code": "missing_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            logger.warning(f"Invalid value: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": "Некорректное значение параметра", "code": "invalid_value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PickupPointNotFound as e:
            logger.warning(f"Pickup point not found: {e.detail}, user={user_id}, path={request.path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except CityNotFound as e:
            logger.warning(f"City not found: {e.detail}, user={user_id}, path={request.path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except ElasticsearchUnavailable as e:
            logger.warning(f"Elasticsearch unavailable: {e.detail}, user={user_id}, path={request.path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except APIException as e:
            logger.warning(f"API error: {e.detail}, user={user_id}, path={request.path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Server error: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper
