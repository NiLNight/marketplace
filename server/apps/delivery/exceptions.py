from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _


class DeliveryServiceException(APIException):
    """Базовое исключение для операций с доставкой."""
    status_code = 400
    default_detail = _("Ошибка при обработке доставки")
    default_code = "delivery_service_error"


class DeliveryNotFound(APIException):
    """Исключение, вызываемое при отсутствии адреса доставки."""
    status_code = 404
    default_detail = _("Адрес доставки не найден")
    default_code = "delivery_not_found"


class PickupPointNotFound(APIException):
    """Исключение, вызываемое при отсутствии или неактивности пункта выдачи."""
    status_code = 404
    default_detail = _("Пункт выдачи не найден или неактивен")
    default_code = "pickup_point_not_found"


class CityNotFound(APIException):
    """Исключение, вызываемое при отсутствии города."""
    status_code = 404
    default_detail = _("Город не найден")
    default_code = "city_not_found"


class ElasticsearchUnavailable(APIException):
    """Исключение, вызываемое при недоступности Elasticsearch."""
    status_code = 503
    default_detail = _("Сервис поиска временно недоступен")
    default_code = "service_unavailable"
