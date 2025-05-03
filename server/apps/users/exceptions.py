from rest_framework.exceptions import APIException


class UserException(APIException):
    """Базовое исключение для операций с пользователями."""
    status_code = 400
    default_detail = 'Ошибка при обработке пользователя'
    default_code = 'user_error'


class UserNotFound(UserException):
    """Исключение, вызываемое при отсутствии пользователя."""
    status_code = 404
    default_detail = 'Пользователь не найден'
    default_code = 'not_found'


class InvalidUserData(UserException):
    """Исключение, вызываемое при некорректных данных пользователя."""
    default_detail = 'Некорректные данные пользователя'
    default_code = 'invalid_data'


class AuthenticationFailed(UserException):
    """Исключение, вызываемое при ошибке аутентификации."""
    status_code = 401
    default_detail = 'Неверные учетные данные'
    default_code = 'authentication_failed'


class AccountNotActivated(UserException):
    """Исключение, вызываемое при попытке входа на неактивированный аккаунт."""
    status_code = 403
    default_detail = 'Аккаунт не активирован'
    default_code = 'account_not_activated'
