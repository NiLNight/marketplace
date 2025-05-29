from rest_framework.exceptions import APIException


class UserException(APIException):
    """Базовое исключение для операций с пользователями.

    Используется как родительский класс для всех исключений, связанных с пользователями.

    Attributes:
        status_code (int): Код HTTP-статуса (400).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 400
    default_detail = 'Ошибка при обработке пользователя'
    default_code = 'user_error'


class UserNotFound(UserException):
    """Исключение, вызываемое при отсутствии пользователя.

    Возникает, когда пользователь с указанными данными не найден в системе.

    Attributes:
        status_code (int): Код HTTP-статуса (404).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 404
    default_detail = 'Пользователь не найден'
    default_code = 'not_found'


class InvalidUserData(UserException):
    """Исключение, вызываемое при некорректных данных пользователя.

    Возникает, когда предоставленные данные пользователя не проходят валидацию.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    default_detail = 'Некорректные данные пользователя'
    default_code = 'invalid_data'


class AuthenticationFailed(UserException):
    """Исключение, вызываемое при ошибке аутентификации.

    Возникает, когда предоставленные учетные данные неверны.

    Attributes:
        status_code (int): Код HTTP-статуса (401).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 401
    default_detail = 'Неверные учетные данные'
    default_code = 'authentication_failed'


class AccountNotActivated(UserException):
    """Исключение, вызываемое при попытке входа на неактивированный аккаунт.

    Возникает, когда пользователь пытается войти, но его аккаунт не подтвержден.

    Attributes:
        status_code (int): Код HTTP-статуса (403).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 403
    default_detail = 'Аккаунт не активирован'
    default_code = 'account_not_activated'
