class CartException(Exception):
    """Базовое исключение для операций с корзиной"""
    default_detail = 'Ошибка корзины'
    status_code = 400

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ProductNotAvailable(CartException):
    default_detail = 'Товар недоступен для заказа'


class InvalidQuantity(CartException):
    default_detail = 'Некорректное количество товара'


class CartItemNotFound(CartException):
    default_detail = 'Элемент корзины не найден'
    status_code = 404


class CheckoutError(CartException):
    default_detail = 'Ошибка оформления заказа'
