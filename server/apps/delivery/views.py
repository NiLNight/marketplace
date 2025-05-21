import logging
from typing import Any
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError as RestValidationError
from django.utils.translation import gettext_lazy as _
import redis
from apps.core.services.cache_services import CacheService
from apps.delivery.models import Delivery, City
from apps.delivery.serializers import DeliverySerializer, PickupPointSerializer, CitySerializer
from apps.delivery.services.delivery_services import DeliveryService
from apps.delivery.services.query_services import DeliveryQueryService, PickupPointQueryService
from apps.delivery.utils import handle_api_errors
from apps.delivery.exceptions import DeliveryServiceException, DeliveryNotFound

logger = logging.getLogger(__name__)


class DeliveryPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


class PickupPointPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 200
    page_size_query_param = 'page_size'


class CityPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 500
    page_size_query_param = 'page_size'


class BaseDeliveryView(APIView):
    pagination_class = DeliveryPagination
    CACHE_TIMEOUT = 300  # 5 минут

    def process_queryset(self, queryset: Any, request: Any, cache_key: str, user_id: str) -> Response:
        try:
            queryset = DeliveryQueryService.get_delivery_list(queryset)
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            serializer = DeliverySerializer(page, many=True)
            response_data = paginator.get_paginated_response(serializer.data).data
            CacheService.set_cached_data(cache_key, response_data, timeout=self.CACHE_TIMEOUT)
            logger.info(f"Retrieved {len(page)} deliveries, user={user_id}")
            return Response(response_data)
        except RestValidationError as e:
            logger.error(f"Validation error processing queryset: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка валидации: {str(e)}")
        except ObjectDoesNotExist as e:
            logger.error(f"Object not found processing queryset: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Объект не найден: {str(e)}")
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error processing queryset: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing queryset: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Неизвестная ошибка обработки списка адресов доставки: {str(e)}")


class DeliveryListView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer

    @handle_api_errors
    def get(self, request):
        user_id = request.user.id
        logger.info(f"Processing delivery list request for user={user_id}")
        try:
            cached_data = CacheService.cache_delivery_list(user_id, request)
            if cached_data:
                logger.info(f"Retrieved cached deliveries for user={user_id}")
                return Response(cached_data)

            deliveries = DeliveryQueryService.get_base_queryset(request.user)
            cache_key = CacheService.build_cache_key(request, prefix=f"delivery_list:{user_id}")
            return self.process_queryset(deliveries, request, cache_key, user_id)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error retrieving delivery list: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")


class DeliveryDetailView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer

    @handle_api_errors
    def get(self, request, pk: int):
        user_id = request.user.id
        logger.info(f"Retrieving delivery {pk}, user={user_id}")
        try:
            cached_data = CacheService.cache_delivery_details(pk, user_id)
            if cached_data:
                return Response(cached_data)

            delivery = DeliveryQueryService.get_single_delivery(pk, request.user)
            serializer = self.serializer_class(delivery)
            cache_key = f'delivery_detail:{pk}:{user_id}'
            CacheService.set_cached_data(cache_key, serializer.data, timeout=7200)
            logger.info(f"Successfully retrieved delivery {pk}, user={user_id}")
            return Response(serializer.data)
        except DeliveryNotFound as e:
            logger.error(f"Delivery {pk} not found: {str(e)}, user={user_id}")
            raise
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error retrieving delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryNotFound(f"Ошибка получения адреса доставки: {str(e)}")


class DeliveryCreateView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer

    @handle_api_errors
    def post(self, request):
        user_id = request.user.id
        logger.info(f"Creating delivery, user={user_id}")
        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            delivery = DeliveryService.create_delivery(serializer.validated_data, request.user)
            CacheService.invalidate_cache(prefix=f"delivery_list:{user_id}")
            logger.info(f"Successfully created delivery {delivery.id}, user={user_id}")
            return Response(
                self.serializer_class(delivery).data,
                status=status.HTTP_201_CREATED
            )
        except RestValidationError as e:
            logger.error(f"Validation error creating delivery: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка валидации адреса доставки: {str(e)}")
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error creating delivery: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating delivery: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка создания адреса доставки: {str(e)}")


class DeliveryUpdateView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySerializer

    @handle_api_errors
    def patch(self, request, pk: int):
        user_id = request.user.id
        logger.info(f"Updating delivery {pk}, user={user_id}")
        try:
            delivery = DeliveryQueryService.get_single_delivery(pk, request.user)
            serializer = self.serializer_class(
                delivery, data=request.data, context={'request': request}, partial=True
            )
            serializer.is_valid(raise_exception=True)
            updated_delivery = DeliveryService.update_delivery(delivery, serializer.validated_data, request.user)
            CacheService.invalidate_cache(prefix=f"delivery_detail:{pk}:{user_id}")
            CacheService.invalidate_cache(prefix=f"delivery_list:{user_id}")
            logger.info(f"Successfully updated delivery {pk}, user={user_id}")
            return Response(self.serializer_class(updated_delivery).data)
        except DeliveryNotFound as e:
            logger.error(f"Delivery {pk} not found: {str(e)}, user={user_id}")
            raise
        except RestValidationError as e:
            logger.error(f"Validation error updating delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка валидации адреса доставки: {str(e)}")
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error updating delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка обновления адреса доставки: {str(e)}")


class DeliveryDeleteView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def delete(self, request, pk: int):
        user_id = request.user.id
        logger.info(f"Deleting delivery {pk}, user={user_id}")
        try:
            delivery = DeliveryQueryService.get_single_delivery(pk, request.user)
            DeliveryService.delete_delivery(delivery, request.user)
            CacheService.invalidate_cache(prefix=f"delivery_detail:{pk}:{user_id}")
            CacheService.invalidate_cache(prefix=f"delivery_list:{user_id}")
            logger.info(f"Successfully deleted delivery {pk}, user={user_id}")
            return Response({"message": "Адрес доставки удален"}, status=status.HTTP_204_NO_CONTENT)
        except DeliveryNotFound as e:
            logger.error(f"Delivery {pk} not found: {str(e)}, user={user_id}")
            raise
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error deleting delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting delivery {pk}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка удаления адреса доставки: {str(e)}")


class PickupPointListView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]
    serializer_class = PickupPointSerializer
    pagination_class = PickupPointPagination
    CACHE_TIMEOUT = 86400  # 24 часа

    @handle_api_errors
    def get(self, request):
        user_id = request.user.id
        logger.info(f"Processing pickup points list request for user={user_id}")
        query = request.GET.get('q', '')
        city_id = request.GET.get('city_id')
        try:
            city_id = int(city_id) if city_id else None
            if city_id and not City.objects.filter(id=city_id).exists():
                logger.warning(f"City with id={city_id} not found for user={user_id}")
                return Response(
                    {"error": _("Город с указанным ID не найден"), "code": "city_not_found"},
                    status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            logger.warning(f"Invalid city_id={city_id} for user={user_id}")
            return Response(
                {"error": _("Идентификатор города должен быть числом"), "code": "invalid_city_id"},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            cached_data = CacheService.cache_pickup_points_list(city_id or 'all', query[:50] or 'none', request)
            if cached_data:
                logger.info(f"Retrieved cached pickup points for user={user_id}")
                return Response(cached_data)

            if query:
                pickup_points = PickupPointQueryService.search_pickup_points(request)
            else:
                pickup_points = PickupPointQueryService.get_base_queryset()
                pickup_points = PickupPointQueryService.apply_filters(pickup_points, request)
                pickup_points = PickupPointQueryService.get_pickup_point_list(pickup_points)
                pickup_points = PickupPointQueryService.apply_ordering(pickup_points, request)

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(pickup_points, request)

            response_data = paginator.get_paginated_response(self.serializer_class(page, many=True).data).data
            cache_key = CacheService.build_cache_key(
                request,
                prefix=f"pickup_points:{city_id or 'all'}:{query[:50] or 'none'}"
            )
            CacheService.set_cached_data(cache_key, response_data, timeout=self.CACHE_TIMEOUT)
            logger.info(f"Retrieved {pickup_points.count()} pickup points for user={user_id}")
            return Response(response_data)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error retrieving pickup points: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")


class CityListView(BaseDeliveryView):
    permission_classes = [IsAuthenticated]
    serializer_class = CitySerializer
    pagination_class = CityPagination

    @handle_api_errors
    def get(self, request):
        user_id = request.user.id
        logger.info(f"Processing city list request for user={user_id}")
        try:
            cached_data = CacheService.cache_city_list(request)
            if cached_data:
                logger.info(f"Retrieved cached cities for user={user_id}")
                return Response(cached_data)

            cities = City.objects.all()
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(cities, request)

            serializer = self.serializer_class(page, many=True).data
            response_data = paginator.get_paginated_response(serializer).data
            cache_key = CacheService.build_cache_key(request, prefix="city_list")
            CacheService.set_cached_data(cache_key, response_data, timeout=86400)
            logger.info(f"Retrieved {cities.count()} cities for user={user_id}")
            return Response(response_data)
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error retrieving city list: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка кэширования: {str(e)}")
