from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _


class PickupPointNotFound(APIException):
    """
    Исключение, вызываемое при отсутствии или неактивности пункта выдачи.

    Attributes:
        status_code (int): Код HTTP-статуса (404).
        default_detail (str): Сообщение об ошибке по умолчанию.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 404
    default_detail = _("Пункт выдачи не найден или неактивен")
    default_code = "pickup_point_not_found"


class CityNotFound(APIException):
    """
    Исключение, вызываемое при отсутствии города.

    Attributes:
        status_code (int): Код HTTP-статуса (404).
        default_detail (str): Сообщение об ошибке по умолчанию.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 404
    default_detail = _("Город не найден")
    default_code = "city_not_found"


class ElasticsearchUnavailable(APIException):
    """
    Исключение, вызываемое при недоступности Elasticsearch.

    Attributes:
        status_code (int): Код HTTP-статуса (503).
        default_detail (str): Сообщение об ошибке по умолчанию.
        default_code (str): Код ошибки по умолчанию.
    """
    status_code = 503
    default_detail = _("Сервис поиска временно недоступен")
    default_code = "service_unavailable"
