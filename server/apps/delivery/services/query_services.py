import logging
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q, Case, When, IntegerField
from elasticsearch_dsl import Search
from typing import Any, Optional, Union
from apps.delivery.models import Delivery, PickupPoint, City
from apps.delivery.exceptions import CityNotFound, ElasticsearchUnavailable, PickupPointNotFound, DeliveryNotFound
from apps.delivery.documents import PickupPointDocument
from apps.delivery.utils import get_filter_params

logger = logging.getLogger(__name__)


class DeliveryQueryService:
    """Сервис для выполнения запросов к адресам доставки."""

    @classmethod
    def get_base_queryset(cls, user: Any) -> Any:
        """Возвращает базовый QuerySet для адресов доставки пользователя."""
        logger.debug(f"Retrieving base queryset for deliveries of user={user.id}")
        return Delivery.objects.filter(user=user)

    @classmethod
    def get_delivery_list(cls, queryset: Any) -> Any:
        """Возвращает список адресов доставки с оптимизированными полями."""
        logger.debug("Applying optimizations for delivery list")
        return queryset.only('id', 'address', 'cost', 'is_primary')

    @classmethod
    def get_single_delivery(cls, pk: int, user: Any) -> Delivery:
        """Получает один адрес доставки по ID."""
        logger.info(f"Retrieving delivery with pk={pk} for user={user.id}")
        try:
            delivery = cls.get_base_queryset(user).get(pk=pk)
            logger.info(f"Retrieved delivery {pk}")
            return delivery
        except Delivery.DoesNotExist:
            logger.warning(f"Delivery {pk} not found for user={user.id}")
            raise DeliveryNotFound("Адрес доставки не найден.")


class PickupPointQueryService:
    """Сервис для выполнения запросов к пунктам выдачи.

    Предоставляет методы для поиска, фильтрации и сортировки пунктов выдачи через Elasticsearch и PostgreSQL.
    """

    ALLOWED_ORDER_FIELDS = {'city__name', 'address', '-city__name', '-address'}
    LARGE_PAGE_SIZE = 200

    @classmethod
    def get_base_queryset(cls) -> Any:
        """Возвращает базовый QuerySet для активных пунктов выдачи."""
        logger.debug("Retrieving base queryset for active pickup points")
        return PickupPoint.objects.filter(is_active=True)

    @classmethod
    def get_pickup_point_list(cls, queryset: Any) -> Any:
        """Возвращает список пунктов выдачи с оптимизированными полями."""
        logger.debug("Applying optimizations for pickup point list")
        return queryset.select_related('city').only(
            'id', 'address', 'is_active', 'city__id', 'city__name'
        )

    @classmethod
    def get_single_pickup_point(cls, pk: int) -> PickupPoint:
        """Получает один пункт выдачи по ID."""
        logger.info(f"Retrieving pickup point with pk={pk}")
        try:
            pickup_point = cls.get_base_queryset().get(pk=pk)
            logger.info(f"Retrieved pickup point {pk}")
            return pickup_point
        except PickupPoint.DoesNotExist:
            logger.warning(f"Pickup point {pk} not found")
            raise PickupPointNotFound("Пункт выдачи не найден.")

    @classmethod
    def apply_common_filters(
            cls,
            source: Union[Any, Search],
            city_id: Optional[int] = None
    ) -> Union[Any, Search]:
        """Применяет общие фильтры к QuerySet или объекту поиска Elasticsearch."""
        logger.debug(f"Applying filters: city_id={city_id}")
        try:
            if isinstance(source, Search):
                if city_id:
                    source = source.filter('term', **{'city.id': city_id})
            else:  # QuerySet
                if city_id:
                    source = source.filter(city_id=city_id)
            return source
        except Exception as e:
            logger.warning(f"Invalid filter parameters: {str(e)}")
            raise CityNotFound(f"Некорректные параметры фильтрации: {str(e)}")

    @classmethod
    def apply_filters(cls, queryset: Any, request: Any) -> Any:
        """Применяет фильтры к QuerySet на основе параметров запроса."""
        logger.debug(f"Applying filters with params={request.GET.dict()}")
        params = get_filter_params(request)
        return cls.apply_common_filters(queryset, **params)

    @classmethod
    def apply_ordering(cls, queryset: Any, request: Any) -> Any:
        """Применяет сортировку к QuerySet на основе параметра запроса."""
        sort_by = request.GET.get('ordering')
        logger.debug(f"Applying ordering with sort_by={sort_by}")
        if sort_by and sort_by not in cls.ALLOWED_ORDER_FIELDS:
            logger.warning(f"Invalid ordering field: {sort_by}")
            sort_by = None
        return queryset.order_by(sort_by or 'city__name', 'address')

    @classmethod
    def search_pickup_points(cls, request: Any) -> Any:
        """Поиск пунктов выдачи в Elasticsearch с фильтрацией и пагинацией."""
        query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        ordering = request.GET.get('ordering', None)
        logger.info(f"Searching pickup points: query={query}, page={page}, page_size={page_size}")

        try:
            if page < 1 or page_size < 1 or page_size > cls.LARGE_PAGE_SIZE:
                logger.warning(f"Invalid pagination params: page={page}, page_size={page_size}")
                raise CityNotFound("Некорректные параметры пагинации.")
            params = get_filter_params(request)
            search = PickupPointDocument.search().filter('term', is_active=True)
            if query:
                search = search.query(
                    'multi_match',
                    query=query,
                    fields=['address^2', 'city.name'],
                    fuzziness='AUTO'
                )
            elif not any(params.values()):
                search = search.sort('city.name', 'address')
            search = cls.apply_common_filters(search, **params)
            if ordering and ordering in cls.ALLOWED_ORDER_FIELDS:
                search = search.sort(ordering)
            elif not query:
                search = search.sort('city.name', 'address')
            if page > 1:
                last_hit = search[0:(page - 1) * page_size][-1]
                search = search.extra(search_after=[last_hit.meta.sort])
            search = search[0:page_size]
            response = search.execute()
            pickup_point_ids = [hit.id for hit in response]
            total = response.hits.total.value if hasattr(response.hits, 'total') else len(pickup_point_ids)
            logger.info(f"Found {len(pickup_point_ids)} pickup points, total={total}")

            preserved_order = Case(
                *[When(id=id, then=pos) for pos, id in enumerate(pickup_point_ids)],
                output_field=IntegerField()
            )
            queryset = cls.get_base_queryset().filter(id__in=pickup_point_ids).annotate(
                order=preserved_order
            ).order_by('order')
            return cls.get_pickup_point_list(queryset)
        except ValueError as e:
            logger.warning(f"Invalid search parameters: {str(e)}")
            raise CityNotFound(f"Некорректные параметры поиска: {str(e)}")
        except Exception as e:
            logger.warning(f"Elasticsearch search failed: {str(e)}, falling back to DB")
            return cls.search_pickup_points_db(cls.get_base_queryset(), request)

    @staticmethod
    def search_pickup_points_db(queryset: Any, request: Any) -> Any:
        """Выполняет поиск пунктов выдачи по текстовому запросу в базе данных."""
        search_query = request.GET.get('q')
        logger.info(f"Searching pickup points with query={search_query}")
        if not search_query:
            logger.warning("Empty search query")
            raise CityNotFound("Пустой поисковый запрос.")
        try:
            query = SearchQuery(search_query, config='russian', search_type='websearch')
            return queryset.annotate(
                rank=SearchRank('search_vector', query)
            ).filter(search_vector=query).order_by('-rank')
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise CityNotFound(f"Ошибка поиска: {str(e)}")
