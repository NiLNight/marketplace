from rest_framework.exceptions import APIException


class CartException(APIException):
    """Базовое исключение для операций с корзиной."""
    default_detail = 'Ошибка корзины'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ProductNotAvailable(CartException):
    """Исключение, если товар недоступен для добавления в корзину."""
    default_detail = 'Товар недоступен для заказа'


class InvalidQuantity(CartException):
    """Исключение, если указано некорректное количество товара."""
    default_detail = 'Некорректное количество товара'


class CartItemNotFound(CartException):
    """Исключение, если элемент не найден в корзине."""
    default_detail = 'Элемент корзины не найден'
    status_code = 404
