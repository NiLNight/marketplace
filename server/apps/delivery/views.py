import logging
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
import redis
from apps.core.services.cache_services import CacheService
from apps.delivery.models import City, PickupPoint
from apps.delivery.serializers import PickupPointSerializer, CitySerializer
from apps.delivery.services.query_services import PickupPointQueryService
from apps.delivery.utils import handle_api_errors

logger = logging.getLogger(__name__)


class PickupPointPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 200
    page_size_query_param = 'page_size'


class CityPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 500
    page_size_query_param = 'page_size'


class PickupPointListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PickupPointSerializer
    pagination_class = PickupPointPagination

    @handle_api_errors
    def get(self, request):
        user_id = request.user.id
        logger.info(f"Processing pickup points list request for user={user_id}")
        query = request.GET.get('q', '')
        city_id = request.GET.get('city_id')
        district = request.GET.get('district')

        cache_key = CacheService.build_cache_key(
            request,
            prefix=f"pickup_points:{city_id or 'all'}:{district or 'none'}:{query[:50] or 'none'}"
        )
        try:
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Retrieved cached pickup points for user={user_id}")
                return Response(cached_data)

            pickup_points = PickupPointQueryService.search_pickup_points(request)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(pickup_points, request)

            response_data = paginator.get_paginated_response(self.serializer_class(page, many=True).data).data
            CacheService.set_cached_data(cache_key, response_data, timeout=60 * 60)
            logger.info(f"Retrieved {pickup_points.count()} pickup points for user={user_id}")
            return Response(response_data)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error retrieving pickup points: {str(e)}, user={user_id}")
            return Response(
                {"error": _("Ошибка кэширования"), "code": "cache_error"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class CityListView(APIView):
    """
    Представление для получения списка городов.

    Поддерживает пагинацию и кэширование.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CityPagination

    def get(self, request):
        """
        Обрабатывает GET-запрос для получения списка городов.

        Args:
            request: HTTP-запрос.

        Returns:
            Response: Список городов с пагинацией.
        """
        logger.info(f"Processing city list request for user={request.user.id}")
        cache_key = CacheService.build_cache_key(request, prefix='city_list')
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Retrieved cached city list for user={request.user.id}")
            return Response(cached_data)

        # Явная сортировка по имени города
        cities = City.objects.all().order_by('name')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(cities, request)
        serializer = CitySerializer(page, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data
        CacheService.set_cached_data(cache_key, response_data, timeout=60 * 60)  # 1 час
        logger.info(f"Retrieved {len(cities)} cities for user={request.user.id}")
        return Response(response_data)


class DistrictListView(APIView):
    permission_classes = [IsAuthenticated]
    CACHE_TIMEOUT = 86400  # 24 часа

    @handle_api_errors
    def get(self, request):
        user_id = request.user.id
        city_id = request.GET.get('city_id')
        logger.info(f"Processing district list request for user={user_id}, city_id={city_id}")

        try:
            if not city_id:
                return Response(
                    {"error": _("Не указан идентификатор города"), "code": "missing_city_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            city_id = int(city_id)
            if not City.objects.filter(id=city_id).exists():
                logger.warning(f"City with id={city_id} not found")
                return Response(
                    {"error": _("Город с указанным ID не найден"), "code": "city_not_found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cache_key = f"districts:{city_id}"
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"Retrieved cached districts for city_id={city_id}, user={user_id}")
                return Response(cached_data)

            districts = PickupPoint.objects.filter(
                city_id=city_id, is_active=True
            ).values('district').distinct().exclude(district__isnull=True).order_by('district')
            districts = [{"name": d['district']} for d in districts]
            response_data = {"results": districts}

            CacheService.set_cached_data(cache_key, response_data, timeout=self.CACHE_TIMEOUT)
            logger.info(f"Retrieved {len(districts)} districts for city_id={city_id}, user={user_id}")
            return Response(response_data)
        except ValueError:
            logger.warning(f"Invalid city_id={city_id} for user={user_id}")
            return Response(
                {"error": _("Идентификатор города должен быть числом"), "code": "invalid_city_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error retrieving districts: {str(e)}, user={user_id}")
            return Response(
                {"error": _("Ошибка кэширования"), "code": "cache_error"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
