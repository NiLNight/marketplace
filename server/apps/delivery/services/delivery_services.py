import logging
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException

from apps.delivery.models import Delivery, PickupPoint, City
from apps.delivery.exceptions import DeliveryNotFound, PickupPointNotFound, CityNotFound

User = get_user_model()
logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Сервис для управления доставкой и пунктами выдачи.

    Предоставляет методы для получения адресов доставки, пунктов выдачи и городов.

    Attributes:
        logger: Логгер для записи событий сервиса.
    """

    @staticmethod
    def get_user_delivery(request, user: User, delivery_id: int) -> Delivery:
        """
        Получает адрес доставки пользователя.

        Проверяет, что пользователь активен и delivery_id является положительным числом.

        Args:
            request: HTTP-запрос для получения IP-адреса.
            user (User): Аутентифицированный пользователь.
            delivery_id (int): Идентификатор адреса доставки.

        Returns:
            Delivery: Объект адреса доставки.

        Raises:
            ValidationError: Если delivery_id некорректен.
            APIException: Если пользователь неактивен.
            DeliveryNotFound: Если адрес доставки не найден или не принадлежит пользователю.
        """
        logger.debug(f"Starting retrieval of delivery={delivery_id} for user={user.id}")
        if not user.is_active:
            logger.warning(
                f"Inactive user={user.id} attempted to access delivery={delivery_id}, IP={request.META.get('REMOTE_ADDR')}")
            raise APIException("Аккаунт не активирован", code="account_not_activated")
        if not isinstance(delivery_id, int) or delivery_id <= 0:
            logger.warning(
                f"Invalid delivery_id={delivery_id} for user={user.id}, IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError("Идентификатор доставки должен быть положительным целым числом")

        logger.info(f"Retrieving delivery={delivery_id} for user={user.id}, IP={request.META.get('REMOTE_ADDR')}")
        try:
            delivery = Delivery.objects.get(pk=delivery_id, user=user)
            logger.info(f"Delivery {delivery_id} retrieved for user={user.id}, IP={request.META.get('REMOTE_ADDR')}")
            return delivery
        except Delivery.DoesNotExist:
            logger.warning(f"Delivery {delivery_id} not found for user={user.id}, IP={request.META.get('REMOTE_ADDR')}")
            raise DeliveryNotFound()

    @staticmethod
    def get_pickup_point(request, pickup_point_id: int) -> PickupPoint:
        """
        Получает пункт выдачи.

        Проверяет, что pickup_point_id является положительным числом.

        Args:
            request: HTTP-запрос для получения IP-адреса.
            pickup_point_id (int): Идентификатор пункта выдачи.

        Returns:
            PickupPoint: Объект пункта выдачи.

        Raises:
            ValidationError: Если pickup_point_id некорректен.
            PickupPointNotFound: Если пункт выдачи не найден или неактивен.
        """
        logger.debug(f"Starting retrieval of pickup point={pickup_point_id}")
        if not isinstance(pickup_point_id, int) or pickup_point_id <= 0:
            logger.warning(f"Invalid pickup_point_id={pickup_point_id}, IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError("Идентификатор пункта выдачи должен быть положительным целым числом")

        logger.info(f"Retrieving pickup point={pickup_point_id}, IP={request.META.get('REMOTE_ADDR')}")
        try:
            pickup_point = PickupPoint.objects.get(pk=pickup_point_id, is_active=True)
            logger.info(f"Pickup point {pickup_point_id} retrieved, IP={request.META.get('REMOTE_ADDR')}")
            return pickup_point
        except PickupPoint.DoesNotExist:
            logger.warning(
                f"Pickup point {pickup_point_id} not found or inactive, IP={request.META.get('REMOTE_ADDR')}")
            raise PickupPointNotFound()

    @staticmethod
    def get_pickup_points(request, city_id: int = None, search: str = None) -> list:
        """
        Получает список пунктов выдачи с фильтрацией.

        Поддерживает фильтрацию по городу и поиск по адресу. Оптимизирует запросы с помощью select_related.

        Args:
            request: HTTP-запрос, содержащий параметры фильтрации.
            city_id (int, optional): Идентификатор города для фильтрации.
            search (str, optional): Поисковая строка для фильтрации по адресу.

        Returns:
            list: Список объектов пунктов выдачи.

        Raises:
            ValidationError: Если параметры некорректны.
            CityNotFound: Если указанный город не найден.
        """
        logger.debug(f"Starting retrieval of pickup points for user={request.user.id}")
        if city_id and (not isinstance(city_id, int) or city_id <= 0):
            logger.warning(
                f"Invalid city_id={city_id} for user={request.user.id}, IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError("Идентификатор города должен быть положительным целым числом")
        if search and len(search) > 100:
            logger.warning(f"Search string too long for user={request.user.id}, IP={request.META.get('REMOTE_ADDR')}")
            raise ValidationError("Поисковая строка не должна превышать 100 символов")

        logger.info(
            f"Retrieving pickup points for user={request.user.id}, city_id={city_id}, search={search}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}"
        )
        queryset = PickupPoint.objects.filter(is_active=True).select_related('city')
        if city_id:
            queryset = queryset.filter(city_id=city_id)
            if not queryset.exists():
                logger.warning(
                    f"No pickup points found for city_id={city_id}, user={request.user.id}, IP={request.META.get('REMOTE_ADDR')}")
                raise CityNotFound()
        if search:
            queryset = queryset.filter(address__icontains=search)
        logger.info(
            f"Retrieved {queryset.count()} pickup points for user={request.user.id}, IP={request.META.get('REMOTE_ADDR')}")
        return queryset

    @staticmethod
    def get_cities() -> list:
        """
        Получает список всех городов.

        Возвращает города, отсортированные по имени.

        Returns:
            list: Список объектов городов.
        """
        logger.debug(f"Starting retrieval of cities")
        logger.info(f"Retrieving cities")
        cities = City.objects.all().order_by('name')
        logger.info(f"Retrieved {cities.count()} cities")
        return cities
