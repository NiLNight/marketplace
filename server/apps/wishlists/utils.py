import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied, APIException
from apps.wishlists.exceptions import WishlistException

logger = logging.getLogger(__name__)


def handle_api_errors(view_func):
    """Декоратор для обработки ошибок в API-представлениях.

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
            logger.error(f"Missing key: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": f"Отсутствует ключ: {str(e)}", "code": "missing_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": str(e), "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": str(e), "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        except WishlistException as e:
            logger.warning(f"Wishlist error: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": e.detail, "code": e.__class__.__name__.lower()},
                status=e.status_code
            )
        except APIException as e:
            logger.error(f"API error: {str(e)}, user={user_id}, path={request.path}")
            return Response(
                {"error": e.detail, "code": e.default_code},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}, user={user_id}, path={request.path}", exc_info=True)
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return wrapper
