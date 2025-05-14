from rest_framework.exceptions import APIException


class DeliveryNotFound(APIException):
    """Исключение, вызываемое при отсутствии адреса доставки."""
    status_code = 404
    default_detail = "Адрес доставки не найден"
    default_code = "delivery_not_found"


class PickupPointNotFound(APIException):
    """Исключение, вызываемое при отсутствии или неактивности пункта выдачи."""
    status_code = 404
    default_detail = "Пункт выдачи не найден или неактивен"
    default_code = "pickup_point_not_found"


class CityNotFound(APIException):
    """Исключение, вызываемое при отсутствии города."""
    status_code = 404
    default_detail = "Город не найден"
    default_code = "city_not_found"
