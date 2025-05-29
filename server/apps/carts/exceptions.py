from rest_framework.exceptions import APIException


class CartException(APIException):
    """Базовое исключение для операций с корзиной.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        status_code (int): Код HTTP-статуса (400).
    """
    default_detail = 'Ошибка корзины'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ProductNotAvailable(CartException):
    """Исключение, если товар недоступен для добавления в корзину.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        status_code (int): Код HTTP-статуса (400, унаследован).
    """
    default_detail = 'Товар недоступен для заказа'


class InvalidQuantity(CartException):
    """Исключение, если указано некорректное количество товара.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        status_code (int): Код HTTP-статуса (400, унаследован).
    """
    default_detail = 'Некорректное количество товара'


class CartItemNotFound(CartException):
    """Исключение, если элемент не найден в корзине.

    Attributes:
        default_detail (str): Сообщение по умолчанию об ошибке.
        status_code (int): Код HTTP-статуса (404).
    """
    default_detail = 'Элемент корзины не найден'
    status_code = 404
