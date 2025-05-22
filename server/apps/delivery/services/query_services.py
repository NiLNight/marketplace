import logging
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Case, When, IntegerField
from elasticsearch_dsl.exceptions import ElasticsearchDslException
from typing import Any
from apps.delivery.models import PickupPoint, City
from apps.delivery.exceptions import CityNotFound
from apps.delivery.documents import PickupPointDocument

logger = logging.getLogger(__name__)


class PickupPointQueryService:
    """Сервис для получения и поиска пунктов выдачи."""

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
            'id', 'address', 'district', 'is_active', 'city__id', 'city__name'
        )

    @classmethod
    def search_pickup_points(cls, request: Any) -> Any:
        """Поиск пунктов выдачи в Elasticsearch с фильтрацией и пагинацией."""
        query = request.GET.get('q', '')
        city_id = request.GET.get('city_id')
        district = request.GET.get('district')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        logger.info(
            f"Searching pickup points: query={query}, city_id={city_id}, district={district}, page={page}, page_size={page_size}")

        try:
            if page < 1 or page_size < 1 or page_size > cls.LARGE_PAGE_SIZE:
                logger.warning(f"Invalid pagination params: page={page}, page_size={page_size}")
                raise CityNotFound("Некорректные параметры пагинации.")

            search = PickupPointDocument.search().filter('term', is_active=True)

            if city_id:
                try:
                    city_id = int(city_id)
                    if not City.objects.filter(id=city_id).exists():
                        logger.warning(f"City with id={city_id} not found")
                        raise CityNotFound(f"Город с ID {city_id} не найден")
                    search = search.filter('term', **{'city.id': city_id})
                except ValueError:
                    logger.warning(f"Invalid city_id={city_id}")
                    raise CityNotFound("Идентификатор города должен быть числом")

            if district:
                search = search.filter('term', **{'district': district})

            if query:
                search = search.query(
                    'multi_match',
                    query=query,
                    fields=['address^2', 'city.name', 'district'],
                    fuzziness='AUTO'
                )
            else:
                search = search.sort('city.name', 'address')

            search = search[(page - 1) * page_size:page * page_size]
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
        except ElasticsearchDslException as e:
            logger.warning(f"Elasticsearch search failed: {str(e)}, falling back to DB")
            return cls.search_pickup_points_db(cls.get_base_queryset(), request)
        except Exception as e:
            logger.error(f"Unexpected error in search_pickup_points: {str(e)}")
            raise CityNotFound(f"Неизвестная ошибка при поиске: {str(e)}")

    @staticmethod
    def search_pickup_points_db(queryset: Any, request: Any) -> Any:
        """Выполняет поиск пунктов выдачи по текстовому запросу в базе данных."""
        query = request.GET.get('q')
        city_id = request.GET.get('city_id')
        district = request.GET.get('district')
        logger.info(f"Searching pickup points in DB: query={query}, city_id={city_id}, district={district}")

        try:
            if city_id:
                city_id = int(city_id)
                if not City.objects.filter(id=city_id).exists():
                    logger.warning(f"City with id={city_id} not found")
                    raise CityNotFound(f"Город с ID {city_id} не найден")
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
            logger.warning(f"Invalid search parameters: {str(e)}")
            raise CityNotFound(f"Некорректные параметры поиска: {str(e)}")
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise CityNotFound(f"Ошибка поиска: {str(e)}")
