# exceptions.py
from rest_framework.exceptions import APIException


class ProductServiceException(APIException):
    status_code = 400
    default_detail = 'Ошибка при обработке продукта'
    default_code = 'product_service_error'


class ProductNotFound(APIException):
    status_code = 404
    default_detail = 'Продукт не найден'
    default_code = 'product_not_found'


class InvalidCategoryError(ProductServiceException):
    default_detail = 'Некорректная категория'
