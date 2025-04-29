from rest_framework.exceptions import APIException


class ProductServiceException(APIException):
    """Базовое исключение для операций с продуктами."""
    status_code = 400
    default_detail = 'Ошибка при обработке продукта'
    default_code = 'product_service_error'


class ProductNotFound(ProductServiceException):
    """Исключение, вызываемое при отсутствии продукта."""
    status_code = 404
    default_detail = 'Продукт не найден'
    default_code = 'product_not_found'


class InvalidCategoryError(ProductServiceException):
    """Исключение, вызываемое при некорректной категории."""
    status_code = 400
    default_detail = 'Некорректная категория'
    default_code = 'invalid_category'


class InvalidProductData(ProductServiceException):
    """Исключение, вызываемое при некорректных данных продукта."""
    status_code = 400
    default_detail = 'Некорректные данные продукта'
    default_code = 'invalid_product_data'
