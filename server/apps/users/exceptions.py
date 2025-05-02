from rest_framework.exceptions import APIException


class UserServiceException(APIException):
    """Базовое исключение для ошибок сервисов пользователей."""
    status_code = 400
    default_detail = "Ошибка в сервисе пользователей."
    default_code = "user_service_error"


class UserNotFound(APIException):
    """Исключение для случая, когда пользователь не найден."""
    status_code = 404
    default_detail = "Пользователь не найден."
    default_code = "user_not_found"
