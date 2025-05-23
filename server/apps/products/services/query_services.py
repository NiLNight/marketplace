import logging

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q, F, Count, Avg, Case, When, IntegerField
from django.db.models.functions import Coalesce, ExtractDay, Now
from elasticsearch_dsl import Search

from apps.products.models import Product, Category
from apps.products.exceptions import ProductNotFound, InvalidCategoryError, ProductServiceException
from apps.products.documents import ProductDocument
from apps.products.utils import get_filter_params
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class ProductQueryService:
    """Сервис для выполнения запросов к продуктам.

    Предоставляет методы для фильтрации, сортировки, поиска продуктов с аннотациями и поиска через Elasticsearch.
    """

    ALLOWED_ORDER_FIELDS = {
        '-popularity_score', 'price', '-price',
        '-created', 'rating_avg', '-rating_avg',
        'popularity_score', 'created'
    }
    LARGE_PAGE_SIZE = 100

    @classmethod
    def get_base_queryset(cls) -> Any:
        """Возвращает базовый QuerySet для активных продуктов.

        Returns:
            QuerySet с активными продуктами.
        """
        logger.debug("Retrieving base queryset for active products")
        return Product.objects.filter(is_active=True)

    @classmethod
    def get_product_list(cls, queryset: Any) -> Any:
        """Возвращает список продуктов с аннотациями и оптимизированными полями.

        Args:
            queryset: QuerySet продуктов.

        Returns:
            QuerySet с аннотациями и выбранными полями.
        """
        logger.debug("Applying annotations for product list")
        return cls._apply_common_annotations(
            queryset
        ).select_related('category').only(
            'title', 'price', 'thumbnail', 'created',
            'discount', 'stock', 'is_active', 'category_id', 'popularity_score'
        )

    @classmethod
    def get_single_product(cls, pk: int) -> Product:
        """Получает один продукт по ID с аннотациями.

        Args:
            pk: Идентификатор продукта.

        Returns:
            Объект Product.

        Raises:
            ProductNotFound: Если продукт не найден.
        """
        logger.info(f"Retrieving product with pk={pk}")
        try:
            product = cls._apply_common_annotations(
                cls.get_base_queryset()
            ).get(pk=pk)
            logger.info(f"Retrieved product {pk}")
            return product
        except Product.DoesNotExist:
            logger.warning(f"Product {pk} not found")
            raise ProductNotFound("Продукт не найден.")

    @staticmethod
    def _apply_common_annotations(queryset: Any) -> Any:
        """Применяет общие аннотации для рейтинга, покупок и популярности.

        Args:
            queryset: QuerySet продуктов.

        Returns:
            QuerySet с аннотациями.
        """
        logger.debug("Applying common annotations")
        return queryset.annotate(
            rating_avg=Coalesce(Avg('reviews__value'), 0.0),
            purchase_count=Count(
                'order_items',
                filter=~Q(order_items__order=None),
                distinct=True
            ),
            review_count=Count('reviews', distinct=True),
            days_since_created=ExtractDay(Now() - F('created'))
        )

    @classmethod
    def apply_common_filters(
            cls,
            source: Union[Any, Search],
            category_id: Optional[int] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            min_discount: Optional[float] = None,
            in_stock: Optional[bool] = None
    ) -> Union[Any, Search]:
        """Применяет общие фильтры к QuerySet или объекту поиска Elasticsearch.

                Args:
                    source: QuerySet (для PostgreSQL) или объект Search (для Elasticsearch).
                    category_id: ID категории для фильтрации.
                    min_price: Минимальная цена (с учётом скидки для Elasticsearch).
                    max_price: Максимальная цена (с учётом скидки для Elasticsearch).
                    min_discount: Минимальная скидка (в процентах).
                    in_stock: Фильтр по наличию на складе.

                Returns:
                    Отфильтрованный QuerySet или объект Search.

                Raises:
                    InvalidCategoryError: Если категория или параметры некорректны.
                """
        logger.debug(f"Applying filters: category_id={category_id}, min_price={min_price}, max_price={max_price}")
        try:
            if isinstance(source, Search):
                if category_id:
                    try:
                        category = Category.objects.get(pk=category_id)
                        descendants = category.get_descendants(include_self=True)
                        source = source.filter('terms', **{'category.id': [c.id for c in descendants]})
                    except Category.DoesNotExist:
                        logger.warning(f"Category {category_id} not found")
                        raise InvalidCategoryError("Категория не найдена.")
                if min_price is not None or max_price is not None:
                    price_range = {}
                    if min_price is not None:
                        price_range['gte'] = min_price
                    if max_price is not None:
                        price_range['lte'] = max_price
                    source = source.filter('range', price_with_discount=price_range)
                if min_discount is not None:
                    source = source.filter('range', discount={'gte': min_discount})
                if in_stock:
                    source = source.filter('range', stock={'gt': 0})
            else:  # PostgreSQL QuerySet
                if category_id:
                    try:
                        category = Category.objects.get(pk=category_id)
                        descendants = category.get_descendants(include_self=True)
                        source = source.filter(category__in=descendants)
                    except Category.DoesNotExist:
                        logger.warning(f"Category {category_id} not found")
                        raise InvalidCategoryError("Категория не найдена.")
                if min_price is not None:
                    source = source.filter(price__gte=min_price)
                if max_price is not None:
                    source = source.filter(price__lte=max_price)
                if min_discount is not None:
                    source = source.filter(discount__gte=min_discount)
                if in_stock:
                    source = source.filter(stock__gt=0)
            return source
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid filter parameters: {str(e)}")
            raise InvalidCategoryError(f"Некорректные параметры фильтрации: {str(e)}")

    @classmethod
    def apply_filters(cls, queryset: Any, request: Any) -> Any:
        """Применяет фильтры к QuerySet на основе параметров запроса.

        Args:
            queryset: QuerySet продуктов.
            request: HTTP-запрос с параметрами фильтрации.

        Returns:
            Отфильтрованный QuerySet.

        Raises:
            InvalidCategoryError: Если параметры фильтрации некорректны.
        """
        logger.debug(f"Applying filters with params={request.GET.dict()}")
        params = get_filter_params(request)
        return cls.apply_common_filters(queryset, **params)

    @classmethod
    def apply_ordering(cls, queryset: Any, request: Any) -> Any:
        """Применяет сортировку к QuerySet на основе параметра запроса.

        Args:
            queryset: QuerySet продуктов.
            request: HTTP-запрос с параметром сортировки.

        Returns:
            Отсортированный QuerySet.
        """
        sort_by = request.GET.get('ordering')
        logger.debug(f"Applying ordering with sort_by={sort_by}")
        if sort_by and sort_by not in cls.ALLOWED_ORDER_FIELDS:
            logger.warning(f"Invalid ordering field: {sort_by}")
            sort_by = None
        return queryset.order_by(sort_by or '-popularity_score')

    @classmethod
    def search_products(cls, request: Any) -> Any:
        """Поиск продуктов в Elasticsearch с фильтрацией и пагинацией.

        Args:
            request: HTTP-запрос с параметрами q, category_id, min_price, max_price, min_discount, in_stock, page, page_size, ordering.

        Returns:
            QuerySet с результатами поиска, сохраняющий порядок из Elasticsearch.

        Raises:
            ProductServiceException: Если поиск не удался или параметры некорректны.
        """
        query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        ordering = request.GET.get('ordering', None)
        logger.info(f"Searching products: query={query}, page={page}, page_size={page_size}")
        try:
            if page < 1 or page_size < 1 or page_size > cls.LARGE_PAGE_SIZE:
                logger.warning(f"Invalid pagination params: page={page}, page_size={page_size}")
                raise ProductServiceException("Некорректные параметры пагинации.")
            params = get_filter_params(request)
            search = ProductDocument.search().filter('term', is_active=True)
            if query:
                search = search.query(
                    'multi_match',
                    query=query,
                    fields=['title^2', 'description', 'category.title'],
                    fuzziness='AUTO'
                )
            elif not any(params.values()):
                search = search.sort('-popularity_score')
            search = cls.apply_common_filters(search, **params)
            if ordering and ordering in cls.ALLOWED_ORDER_FIELDS:
                search = search.sort(ordering)
            elif not query:
                search = search.sort('-popularity_score')
            if page > 1:
                last_hit = search[0:(page - 1) * page_size][-1]
                search = search.extra(search_after=[last_hit.meta.sort])
            search = search[0:page_size]
            response = search.execute()
            product_ids = [hit.id for hit in response]
            total = response.hits.total.value if hasattr(response.hits, 'total') and hasattr(response.hits.total,
                                                                                             'value') else len(
                product_ids)
            logger.info(f"Found {len(product_ids)} products, total={total}")
            preserved_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(product_ids)],
                                   output_field=IntegerField())
            queryset = cls.get_base_queryset().filter(id__in=product_ids).annotate(order=preserved_order).order_by(
                'order')
            return queryset
        except ValueError as e:
            logger.warning(f"Invalid search parameters: {str(e)}")
            raise ProductServiceException(f"Некорректные параметры поиска: {str(e)}")
        except Exception as e:
            logger.exception(f"Failed to search products: {str(e)}")
            raise ProductServiceException(f"Ошибка поиска продуктов: {str(e)}")

    @staticmethod
    def search_products_db(queryset: Any, request: Any) -> Any:
        """Выполняет поиск продуктов по текстовому запросу в базе данных.

        Args:
            queryset: QuerySet продуктов.
            request: HTTP-запрос с поисковым запросом.

        Returns:
            QuerySet с результатами поиска, отсортированный по релевантности.

        Raises:
            ProductServiceException: Если поисковый запрос пустой или некорректен.
        """
        search_query = request.GET.get('q')
        logger.info(f"Searching products with query={search_query}")
        if not search_query:
            logger.warning("Empty search query")
            raise ProductServiceException("Пустой поисковый запрос.")
        try:
            query = SearchQuery(search_query, config='russian', search_type='websearch')
            return queryset.annotate(
                rank=SearchRank('search_vector', query)
            ).filter(search_vector=query).order_by('-rank')
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise ProductServiceException(f"Ошибка поиска: {str(e)}")
