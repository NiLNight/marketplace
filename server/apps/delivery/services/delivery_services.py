import logging
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from apps.delivery.models import City
from apps.delivery.services.query_services import PickupPointQueryService
from apps.delivery.serializers import SearchSerializer

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Сервис для управления доставкой: получение пунктов выдачи, городов и районов.

    Реализует бизнес-логику, включая проверки прав доступа и валидацию данных.
    """

    @staticmethod
    def get_pickup_points(request):
        """
        Получает список пунктов выдачи с учетом фильтров и пагинации.

        Args:
            request (HttpRequest): Объект HTTP-запроса.

        Returns:
            QuerySet: Список пунктов выдачи.

        Raises:
            CityNotFound: Если параметры фильтрации некорректны или город не найден.
            PermissionDenied: Если пользователь не аутентифицирован.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if not request.user.is_authenticated:
            raise PermissionDenied(_("Доступ запрещен: требуется аутентификация"))

        serializer = SearchSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data.get('query', '')
        city_id = request.GET.get('city_id')
        district = request.GET.get('district')
        page = request.GET.get('page', '1')
        page_size = request.GET.get('page_size', '50')
        logger.info(
            f"Action=GetPickupPoints UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}, Query={query}, "
            f"CityID={city_id}, District={district}, Page={page}, PageSize={page_size}"
        )
        pickup_points = PickupPointQueryService.search_pickup_points(request)
        return pickup_points

    @staticmethod
    def get_cities(request):
        """
        Получает список всех городов.

        Args:
            request (HttpRequest): Объект HTTP-запроса.

        Returns:
            QuerySet: Список городов.

        Raises:
            CityNotFound: Если произошла ошибка при получении городов.
            PermissionDenied: Если пользователь не аутентифицирован.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if not request.user.is_authenticated:
            raise PermissionDenied(_("Доступ запрещен: требуется аутентификация"))
        logger.info(
            f"Action=GetCities UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        return City.objects.all().only("id", "name").order_by("name")
