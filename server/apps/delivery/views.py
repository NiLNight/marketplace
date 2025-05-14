import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.services.cache_services import CacheService
from apps.delivery.models import Delivery
from apps.delivery.serializers import DeliverySerializer, PickupPointSerializer, CitySerializer
from apps.delivery.services.delivery_services import DeliveryService
from apps.delivery.utils import handle_api_errors

logger = logging.getLogger(__name__)


class DeliveryPagination(PageNumberPagination):
    """Класс пагинации для списка адресов доставки."""
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


class PickupPointPagination(PageNumberPagination):
    """Класс пагинации для списка пунктов выдачи."""
    page_size = 50
    max_page_size = 200
    page_size_query_param = 'page_size'


class CityPagination(PageNumberPagination):
    """Класс пагинации для списка городов."""
    page_size = 100
    max_page_size = 500
    page_size_query_param = 'page_size'


class DeliveryListView(APIView):
    """Представление для получения списка адресов доставки пользователя."""
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer
    pagination_class = DeliveryPagination

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения списка адресов доставки.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Ответ с данными адресов доставки или ошибкой.
        """
        user_id = request.user.id
        cache_key = CacheService.build_cache_key(request, prefix=f"delivery_list:{user_id}")
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            logger.info(
                f"Retrieved cached deliveries for user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(cached_data)

        deliveries = Delivery.objects.filter(user=request.user)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(deliveries, request)

        serializer = self.serializer_class(page, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data
        CacheService.set_cached_data(cache_key, response_data, timeout=840)  # 14 минут
        logger.info(
            f"Retrieved {len(deliveries)} deliveries for user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        return Response(response_data)


class PickupPointListView(APIView):
    """Представление для получения списка пунктов выдачи."""
    permission_classes = [IsAuthenticated]
    serializer_class = PickupPointSerializer
    pagination_class = PickupPointPagination

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения списка пунктов выдачи.

        Поддерживает фильтрацию по городу и поиск по адресу.

        Args:
            request (HttpRequest): Объект запроса с параметрами фильтрации.

        Returns:
            Response: Ответ с данными пунктов выдачи или ошибкой.
        """
        user_id = request.user.id
        city_id = request.GET.get('city_id')
        search = request.GET.get('search')
        cache_key = CacheService.build_cache_key(
            request, prefix=f"pickup_points:{city_id or 'all'}:{search or 'none'}"
        )
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            logger.info(
                f"Retrieved cached pickup points for user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(cached_data)

        pickup_points = DeliveryService.get_pickup_points(request, city_id=city_id, search=search)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(pickup_points, request)

        response_data = paginator.get_paginated_response(self.serializer_class(page, many=True).data).data
        CacheService.set_cached_data(cache_key, response_data, timeout=86400)  # 24 часа
        logger.info(
            f"Retrieved {pickup_points.count()} pickup points for user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        return Response(response_data)


class CityListView(APIView):
    """Представление для получения списка городов."""
    permission_classes = [IsAuthenticated]
    serializer_class = CitySerializer
    pagination_class = CityPagination

    @handle_api_errors
    def get(self, request):
        """Обрабатывает GET-запрос для получения списка городов.

        Args:
            request (HttpRequest): Объект запроса.

        Returns:
            Response: Ответ с данными городов или ошибкой.
        """
        user_id = request.user.id
        cache_key = CacheService.build_cache_key(request, prefix="city_list")
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            logger.info(
                f"Retrieved cached cities for user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
            return Response(cached_data)

        cities = DeliveryService.get_cities()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(cities, request)

        serializer = self.serializer_class(page, many=True).data
        response_data = paginator.get_paginated_response(serializer).data
        CacheService.set_cached_data(cache_key, response_data, timeout=86400)  # 24 часа
        logger.info(
            f"Retrieved {cities.count()} cities for user={user_id}, path={request.path}, IP={request.META.get('REMOTE_ADDR')}")
        return Response(response_data)
