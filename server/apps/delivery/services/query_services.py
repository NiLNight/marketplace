import logging
import time
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Case, When, IntegerField
from elasticsearch_dsl.exceptions import ElasticsearchDslException
from typing import Any
from apps.delivery.models import PickupPoint, City
from apps.delivery.exceptions import CityNotFound, ElasticsearchUnavailable
from apps.delivery.documents import PickupPointDocument
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class PickupPointQueryService:
    """
    Сервис для выполнения запросов к пунктам выдачи.

    Использует Elasticsearch для полнотекстового поиска и PostgreSQL как запасной вариант.
    """
    LARGE_PAGE_SIZE = 200
    MAX_QUERY_LENGTH = 255
    MAX_DISTRICT_LENGTH = 100

    @classmethod
    def get_base_queryset(cls) -> Any:
        """
        Возвращает базовый QuerySet для активных пунктов выдачи.

        Args:
            cls: Класс сервиса.

        Returns:
            QuerySet: Активные пункты выдачи.
        """
        logger.info("Action=GetBaseQueryset")
        return PickupPoint.objects.filter(is_active=True)

    @classmethod
    def get_pickup_point_list(cls, queryset: Any) -> Any:
        """
        Оптимизирует QuerySet пунктов выдачи, исключая ненужные поля.

        Args:
            cls: Класс сервиса.
            queryset (QuerySet): Исходный QuerySet пунктов выдачи.

        Returns:
            QuerySet: Оптимизированный QuerySet с выбранными полями.
        """
        logger.info("Action=OptimizePickupPointList")
        return queryset.select_related('city').only(
            'id', 'address', 'district', 'is_active', 'city__id', 'city__name'
        )

    @classmethod
    def search_pickup_points(cls, request: Any) -> Any:
        """
        Выполняет поиск пунктов выдачи в Elasticsearch с фильтрацией и пагинацией.

        Args:
            cls: Класс сервиса.
            request (HttpRequest): HTTP-запрос с параметрами поиска.

        Returns:
            QuerySet: Список пунктов выдачи.

        Raises:
            CityNotFound: Если параметры поиска некорректны или город не найден.
            ElasticsearchUnavailable: Если Elasticsearch недоступен.
            PermissionDenied: Если пользователь не аутентифицирован.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        if not request.user.is_authenticated:
            raise PermissionDenied(_("Доступ запрещен: требуется аутентификация"))
        query = request.GET.get('q', '')[:cls.MAX_QUERY_LENGTH]
        city_id = request.GET.get('city_id')
        district = request.GET.get('district')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        start_time = time.time()
        logger.info(
            f"Action=SearchPickupPoints UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}, Query={query}, "
            f"CityID={city_id}, District={district}, Page={page}, PageSize={page_size}"
        )

        try:
            if page < 1 or page_size < 1 or page_size > cls.LARGE_PAGE_SIZE:
                logger.warning(
                    f"Invalid pagination parameters Page={page}, PageSize={page_size}, "
                    f"UserID={user_id}, Path={request.path}, IP={request.META.get('REMOTE_ADDR', 'unknown')}"
                )
                raise CityNotFound(
                    detail=_("Некорректные параметры пагинации"),
                    code="invalid_pagination"
                )

            search = PickupPointDocument.search()
            if not request.user.is_staff:
                search = search.filter('term', is_active=True)
            if city_id:
                try:
                    city_id = int(city_id)
                    if not City.objects.filter(id=city_id).exists():
                        logger.warning(
                            f"City not found CityID={city_id}, UserID={user_id}, "
                            f"Path={request.path}, IP={request.META.get('REMOTE_ADDR', 'unknown')}"
                        )
                        raise CityNotFound(
                            detail=_("Город с указанным ID не найден"),
                            code="city_not_found"
                        )
                    search = search.filter('term', **{'city.id': city_id})
                except ValueError:
                    logger.warning(
                        f"Invalid city_id={city_id}, UserID={user_id}, Path={request.path}, "
                        f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
                    )
                    raise CityNotFound(
                        detail=_("Идентификатор города должен быть числом"),
                        code="invalid_city_id"
                    )

            if district:
                search = search.filter('term', **{'district': district})

            if query:
                search = search.query(
                    'multi_match',
                    query=query,
                    fields=['address^2', 'city.name', 'district'],
                    fuzziness=2
                )
            else:
                search = search.sort('city.name', 'address')

            search = search[(page - 1) * page_size:page * page_size]
            response = search.execute()
            pickup_point_ids = [hit.id for hit in response]
            try:
                total = response.hits.total.value
            except AttributeError:
                total = len(pickup_point_ids)
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"Found {len(pickup_point_ids)} pickup points, Total={total}, UserID={user_id}, "
                f"Path={request.path}, IP={request.META.get('REMOTE_ADDR', 'unknown')}, "
                f"duration_ms={duration:.2f}"
            )

            if not pickup_point_ids:
                logger.info(
                    f"No pickup points found, UserID={user_id}, Path={request.path}, "
                    f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
                )
                return cls.get_pickup_point_list(cls.get_base_queryset().none())

            preserved_order = Case(
                *[When(id=id, then=pos) for pos, id in enumerate(pickup_point_ids)],
                output_field=IntegerField()
            )
            queryset = cls.get_base_queryset().filter(id__in=pickup_point_ids).annotate(
                order=preserved_order
            ).order_by('order')
            return cls.get_pickup_point_list(queryset)
        except ElasticsearchDslException as e:
            logger.warning(
                f"Elasticsearch search failed: {str(e)}, UserID={user_id}, Path={request.path}, "
                f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            raise ElasticsearchUnavailable(
                detail=_("Сервис поиска временно недоступен"),
                code="service_unavailable"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in search_pickup_points: {str(e)}, UserID={user_id}, "
                f"Path={request.path}, IP={request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            raise CityNotFound(
                detail=_("Неизвестная ошибка при поиске"),
                code="search_error"
            )

    @staticmethod
    def search_pickup_points_db(queryset: Any, request: Any) -> Any:
        """
        Выполняет поиск пунктов выдачи в PostgreSQL.

        Args:
            queryset (QuerySet): Базовый QuerySet пунктов выдачи.
            request (HttpRequest): HTTP-запрос с параметрами поиска.

        Returns:
            QuerySet: Список пунктов выдачи.

        Raises:
            CityNotFound: Если параметры поиска некорректны или город не найден.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        query = request.GET.get('q', '')[:PickupPointQueryService.MAX_QUERY_LENGTH]
        city_id = request.GET.get('city_id')
        district = request.GET.get('district')
        if district:
            if len(district) > PickupPointQueryService.MAX_DISTRICT_LENGTH or not district.strip():
                logger.warning(
                    f"Invalid district length or empty: {len(district)}, UserID={user_id}, "
                    f"Path={request.path}, IP={request.META.get('REMOTE_ADDR', 'unknown')}"
                )
                raise CityNotFound(
                    detail=_("Некорректный район"),
                    code="invalid_district"
                )
        logger.info(
            f"Action=SearchPickupPointsDB UserID={user_id}, Path={request.path}, "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}, Query={query}, "
            f"CityID={city_id}, District={district}"
        )

        try:
            if city_id:
                city_id = int(city_id)
                if not City.objects.filter(id=city_id).exists():
                    logger.warning(
                        f"City not found CityID={city_id}, UserID={user_id}, Path={request.path}, "
                        f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
                    )
                    raise CityNotFound(
                        detail=_("Город с указанным ID не найден"),
                        code="city_not_found"
                    )
                queryset = queryset.filter(city_id=city_id)

            if district:
                queryset = queryset.filter(district=district)

            if query:
                search_query = SearchQuery(query, config='russian', search_type='websearch')
                queryset = queryset.annotate(
                    rank=SearchRank('search_vector', search_query)
                ).filter(search_vector=search_query).order_by('-rank')
            else:
                queryset = queryset.order_by('city__name', 'address')

            return queryset
        except ValueError as e:
            logger.warning(
                f"Invalid search parameters: {str(e)}, UserID={user_id}, Path={request.path}, "
                f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            raise CityNotFound(
                detail=_("Некорректные параметры поиска"),
                code="invalid_search_params"
            )
        except Exception as e:
            logger.error(
                f"Search failed: {str(e)}, UserID={user_id}, Path={request.path}, "
                f"IP={request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            raise CityNotFound(
                detail=_("Ошибка поиска"),
                code="search_error"
            )
