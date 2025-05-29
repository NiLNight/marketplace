from rest_framework.exceptions import APIException


class ProductServiceException(APIException):
    """Базовое исключение для операций с продуктами.

    Attributes:
        status_code (int): Код HTTP-статуса (400).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 400
    default_detail = 'Ошибка при обработке продукта'
    default_code = 'product_service_error'


class ProductNotFound(ProductServiceException):
    """Исключение, вызываемое при отсутствии продукта.

    Attributes:
        status_code (int): Код HTTP-статуса (404).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 404
    default_detail = 'Продукт не найден'
    default_code = 'product_not_found'


class InvalidCategoryError(ProductServiceException):
    """Исключение, вызываемое при некорректной категории.

    Attributes:
        status_code (int): Код HTTP-статуса (400).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 400
    default_detail = 'Некорректная категория'
    default_code = 'invalid_category'


class InvalidProductData(ProductServiceException):
    """Исключение, вызываемое при некорректных данных продукта.

    Attributes:
        status_code (int): Код HTTP-статуса (400).
        default_detail (str): Сообщение по умолчанию об ошибке.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 400
    default_detail = 'Некорректные данные продукта'
    default_code = 'invalid_product_data'
