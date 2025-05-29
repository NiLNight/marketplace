from rest_framework.exceptions import APIException


class WishlistException(APIException):
    """Базовое исключение для операций со списком желаний.

    Attributes:
        default_detail (str): Сообщение об ошибке по умолчанию.
        status_code (int): HTTP-код статуса для ошибки (400).
        detail (str): Конкретное сообщение об ошибке.
    """
    default_detail = 'Ошибка списка желаний'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ProductNotAvailable(WishlistException):
    """Исключение, если товар недоступен для добавления в список желаний.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        status_code (int): Код HTTP-статуса (400, унаследован).
    """
    default_detail = 'Товар недоступен для списка желаний'


class WishlistItemNotFound(WishlistException):
    """Исключение, если элемент не найден в списке желаний.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        status_code (int): Код HTTP-статуса (404).
    """
    default_detail = 'Элемент списка желаний не найден'
    status_code = 404