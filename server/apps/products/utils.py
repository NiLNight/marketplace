import logging
from typing import Dict, Any
from django.http import HttpRequest
from django.db.models import Avg
from django.utils import timezone
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException, PermissionDenied
from apps.products.exceptions import ProductServiceException, ProductNotFound, InvalidCategoryError, InvalidProductData

logger = logging.getLogger(__name__)


def get_filter_params(request: HttpRequest) -> Dict[str, Any]:
    params = request.GET
    result = {
        'category_id': None,
        'min_price': None,
        'max_price': None,
        'min_discount': None,
        'in_stock': None,
    }
    try:
        # Проверяем category_id или category
        category_value = next((params.get(key) for key in ('category_id', 'category') if params.get(key) is not None),
                              None)
        if category_value is not None:
            result['category_id'] = int(category_value)

        # Проверяем min_price или price__gte
        min_price_value = next((params.get(key) for key in ('min_price', 'price__gte') if params.get(key) is not None),
                               None)
        if min_price_value is not None:
            result['min_price'] = float(min_price_value)

        # Проверяем max_price или price__lte
        max_price_value = next((params.get(key) for key in ('max_price', 'price__lte') if params.get(key) is not None),
                               None)
        if max_price_value is not None:
            result['max_price'] = float(max_price_value)

        # Проверяем min_discount
        min_discount = params.get('min_discount')
        if min_discount is not None:
            result['min_discount'] = float(min_discount)

        # Проверяем in_stock
        in_stock = params.get('in_stock')
        if in_stock is not None:
            result['in_stock'] = in_stock.lower() == 'true'

        return result
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid filter parameters: {str(e)}")
        raise ProductServiceException(f"Некорректные параметры фильтрации: {str(e)}")


def calculate_popularity_score(product) -> float:
    purchase_count = product.order_items.filter(order__status='delivered').count()
    review_count = product.reviews.count()
    rating_avg = product.reviews.aggregate(Avg('value'))['value__avg'] or 0.0
    days_since_created = (timezone.now() - product.created).days + 1
    return (
            (purchase_count * 0.4) +
            (review_count * 0.2) +
            (rating_avg * 0.3) +
            (1 / days_since_created * 0.1)
    )


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях приложения products.

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
        except ProductNotFound as e:
            logger.warning(f"Product not found: {e.detail}, user={user_id}, path={path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except (ProductServiceException, InvalidCategoryError, InvalidProductData) as e:
            logger.warning(f"Product error: {e.detail}, user={user_id}, path={path}")
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
