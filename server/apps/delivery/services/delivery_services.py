import logging
from django.contrib.auth import get_user_model
from apps.delivery.models import Delivery, PickupPoint, City
from apps.delivery.exceptions import DeliveryNotFound, PickupPointNotFound, CityNotFound

User = get_user_model()
logger = logging.getLogger(__name__)


class DeliveryService:
    """Сервис для управления доставкой и пунктами выдачи.

    Предоставляет методы для получения адресов доставки, пунктов выдачи и городов.
    """

    @staticmethod
    def get_user_delivery(user: User, delivery_id: int) -> Delivery:
        """Получает адрес доставки пользователя.

        Args:
            user (User): Аутентифицированный пользователь.
            delivery_id (int): Идентификатор адреса доставки.

        Returns:
            Delivery: Объект адреса доставки.

        Raises:
            DeliveryNotFound: Если адрес доставки не найден или не принадлежит пользователю.
        """
        logger.info(f"Retrieving delivery={delivery_id} for user={user.id}")
        try:
            delivery = Delivery.objects.get(pk=delivery_id, user=user)
            logger.info(f"Delivery {delivery_id} retrieved for user={user.id}")
            return delivery
        except Delivery.DoesNotExist:
            logger.warning(f"Delivery {delivery_id} not found for user={user.id}")
            raise DeliveryNotFound()

    @staticmethod
    def get_pickup_point(pickup_point_id: int) -> PickupPoint:
        """Получает пункт выдачи.

        Args:
            pickup_point_id (int): Идентификатор пункта выдачи.

        Returns:
            PickupPoint: Объект пункта выдачи.

        Raises:
            PickupPointNotFound: Если пункт выдачи не найден или неактивен.
        """
        logger.info(f"Retrieving pickup point={pickup_point_id}")
        try:
            pickup_point = PickupPoint.objects.get(pk=pickup_point_id, is_active=True)
            logger.info(f"Pickup point {pickup_point_id} retrieved")
            return pickup_point
        except PickupPoint.DoesNotExist:
            logger.warning(f"Pickup point {pickup_point_id} not found or inactive")
            raise PickupPointNotFound()

    @staticmethod
    def get_pickup_points(request, city_id: int = None, search: str = None) -> list:
        """Получает список пунктов выдачи с фильтрацией.

        Args:
            request: HTTP-запрос, содержащий параметры фильтрации.
            city_id (int, optional): Идентификатор города для фильтрации.
            search (str, optional): Поисковая строка для фильтрации по адресу.

        Returns:
            list: Список объектов пунктов выдачи.

        Raises:
            CityNotFound: Если указанный город не найден.
        """
        logger.info(
            f"Retrieving pickup points for user={request.user.id}, city_id={city_id}, search={search}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        queryset = PickupPoint.objects.filter(is_active=True)
        if city_id:
            if not City.objects.filter(id=city_id).exists():
                logger.warning(f"City {city_id} not found for user={request.user.id}")
                raise CityNotFound()
            queryset = queryset.filter(city_id=city_id)
        if search:
            queryset = queryset.filter(address__icontains=search)
        logger.info(f"Retrieved {queryset.count()} pickup points for user={request.user.id}")
        return queryset

    @staticmethod
    def get_cities() -> list:
        """Получает список всех городов.

        Returns:
            list: Список объектов городов.
        """
        logger.info(f"Retrieving cities")
        cities = City.objects.all().order_by('name')
        logger.info(f"Retrieved {cities.count()} cities")
        return cities
