import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.services.cache_services import CacheService
from apps.delivery.services.delivery_services import DeliveryService
from apps.delivery.serializers import PickupPointSerializer, CitySerializer
from apps.delivery.utils import handle_api_errors

logger = logging.getLogger(__name__)


class PickupPointPagination(PageNumberPagination):
    """
    Пагинация для списка пунктов выдачи.

    Attributes:
        page_size (int): Размер страницы по умолчанию.
        max_page_size (int): Максимальный размер страницы.
        page_size_query_param (str): Параметр для указания размера страницы.
    """
    page_size = 50
    max_page_size = 200
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Пагинирует QuerySet с проверкой размера страницы.

        Args:
            queryset (QuerySet): QuerySet для пагинации.
            request (HttpRequest): HTTP-запрос.
            view (APIView, optional): Представление.

        Returns:
            list: Пагинированный список.

        Raises:
            ValidationError: Если размер страницы превышает максимальный.
        """
        page_size = self.get_page_size(request)
        if page_size > self.max_page_size:
            raise ValidationError(
                _("Размер страницы не может превышать {max_page_size}").format(
                    max_page_size=self.max_page_size
                )
            )
        return super().paginate_queryset(queryset, request, view)


class CityPagination(PageNumberPagination):
    """
    Пагинация для списка городов.

    Attributes:
        page_size (int): Размер страницы по умолчанию.
        max_page_size (int): Максимальный размер страницы.
        page_size_query_param (str): Параметр для указания размера страницы.
    """
    page_size = 100
    max_page_size = 500
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Пагинирует QuerySet с проверкой размера страницы.

        Args:
            queryset (QuerySet): QuerySet для пагинации.
            request (HttpRequest): HTTP-запрос.
            view (APIView, optional): Представление.

        Returns:
            list: Пагинированный список.

        Raises:
            ValidationError: Если размер страницы превышает максимальный.
        """
        page_size = self.get_page_size(request)
        if page_size > self.max_page_size:
            raise ValidationError(
                _("Размер страницы не может превышать {max_page_size}").format(
                    max_page_size=self.max_page_size
                )
            )
        return super().paginate_queryset(queryset, request, view)


class PickupPointListView(APIView):
    """
    Представление для получения списка пунктов выдачи.

    Поддерживает поиск, фильтрацию, пагинацию и кэширование через CacheService.

    Attributes:
        permission_classes (list): Требует аутентификации пользователя.
        throttle_classes (list): Ограничение частоты запросов для анонимных пользователей.
        pagination_class (PageNumberPagination): Класс пагинации.
        serializer_class (Serializer): Сериализатор для пунктов выдачи.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle]  # Добавлен rate limiting
    pagination_class = PickupPointPagination
    serializer_class = PickupPointSerializer

    @handle_api_errors
    def get(self, request):
        """
        Обрабатывает GET-запрос для получения списка пунктов выдачи.

        Args:
            request (HttpRequest): HTTP-запрос.

        Returns:
            Response: Пагинированный список пунктов выдачи.

        Raises:
            ValidationError: Если параметры запроса некорректны.
            CityNotFound: Если город не найден.
            ElasticsearchUnavailable: Если сервис поиска недоступен.
        """
        user_id = request.user.id
        city_id = request.GET.get('city_id', None)
        search = request.GET.get('q', '')
        page = request.GET.get('page', '1')
        page_size = request.GET.get('page_size', '50')
        logger.info(
            f"Action=GetPickupPointsList UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}, Query={search}, "
            f"CityID={city_id}, Page={page}, PageSize={page_size}"
        )

        # Проверка кэша
        cached_data = CacheService.cache_pickup_points_list(request, city_id)
        if cached_data:
            logger.info(
                f"Retrieved cached pickup points CityID={city_id}, Search={search}, "
                f"UserID={user_id}, Path={request.path}, IP={request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            return Response(cached_data)

        # Получение данных
        pickup_points = DeliveryService.get_pickup_points(request)
        paginator = self.pagination_class()
        page_data = paginator.paginate_queryset(pickup_points, request)
        serializer = self.serializer_class(page_data, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data

        # Кэширование результата
        CacheService.set_cached_data(
            CacheService.build_cache_key(request, prefix=f"pickup_points:{city_id or 'all'}"),
            response_data,
            timeout=86400
        )
        logger.info(
            f"Retrieved {len(page_data)} pickup points UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        return Response(response_data)


class CityListView(APIView):
    """
    Представление для получения списка городов.

    Поддерживает пагинацию и кэширование через CacheService.

    Attributes:
        permission_classes (list): Требует аутентификации пользователя.
        throttle_classes (list): Ограничение частоты запросов для анонимных пользователей.
        pagination_class (PageNumberPagination): Класс пагинации.
        serializer_class (Serializer): Сериализатор для городов.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle]  # Добавлен rate limiting
    pagination_class = CityPagination
    serializer_class = CitySerializer

    @handle_api_errors
    def get(self, request):
        """
        Обрабатывает GET-запрос для получения списка городов.

        Args:
            request (HttpRequest): HTTP-запрос.

        Returns:
            Response: Пагинированный список городов.

        Raises:
            CityNotFound: Если произошла ошибка при получении городов.
        """
        user_id = request.user.id
        page = request.GET.get('page', '1')
        page_size = request.GET.get('page_size', '100')
        logger.info(
            f"Action=GetCityList UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}, Page={page}, PageSize={page_size}"
        )

        # Проверка кэша
        cached_data = CacheService.cache_city_list(request)
        if cached_data:
            logger.info(
                f"Retrieved cached city list UserID={user_id}, Path={request.path}, "
                f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            return Response(cached_data)

        # Получение данных
        cities = DeliveryService.get_cities(request)
        paginator = self.pagination_class()
        page_data = paginator.paginate_queryset(cities, request)
        serializer = self.serializer_class(page_data, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data

        # Кэширование результата
        CacheService.set_cached_data(
            CacheService.build_cache_key(request, prefix="city_list"),
            response_data,
            timeout=3600
        )
        logger.info(
            f"Retrieved {len(page_data)} cities UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        return Response(response_data)
