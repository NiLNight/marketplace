import logging

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q, F, Count, Avg, Case, When, IntegerField
from django.db.models.functions import Coalesce, ExtractDay, Now
from elasticsearch_dsl import Search
from django.conf import settings

from apps.products.models import Product, Category
from apps.products.exceptions import ProductNotFound, InvalidCategoryError, ProductServiceException
from apps.products.documents import ProductDocument
from apps.products.utils import get_filter_params
from typing import Any, Optional, Union
from django.db.models import QuerySet

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
    def get_base_queryset(cls, request: Any) -> QuerySet:
        """Возвращает базовый QuerySet для продуктов.

        В тестовом режиме возвращает все продукты, в production только активные.

        Returns:
            QuerySet: Базовый QuerySet с продуктами.
        """
        logger.debug("Retrieving base queryset for active products")
        my_products = request.GET.get('my_products', None)
        if settings.TESTING:
            return Product.objects.all()
        elif my_products:
            return Product.objects.filter(
                user=request.user) \
                if (my_products == 'true' and
                    request.user.is_authenticated) else Product.objects.none()
        return Product.objects.filter(is_active=True)

    @classmethod
    def get_product_list(cls, request: Any, queryset: Optional[Any] = None) -> Any:
        """Возвращает список продуктов с аннотациями и оптимизированными полями.

        Args:
            request: Request
            queryset: QuerySet продуктов. Если не указан, используется базовый queryset.

        Returns:
            QuerySet с аннотациями и выбранными полями.
        """
        logger.debug("Applying annotations for product list")
        if queryset is None:
            queryset = cls.get_base_queryset(request)
        return cls._apply_common_annotations(
            queryset
        ).select_related('category').only(
            'title', 'price', 'thumbnail', 'created',
            'discount', 'stock', 'is_active', 'category_id', 'popularity_score'
        )

    @classmethod
    def get_single_product(cls, pk: int, request: Any) -> Product:
        """Получает один продукт по ID с аннотациями.

        Args:
            pk: Идентификатор продукта.
            request: Request

        Returns:
            Объект Product.

        Raises:
            ProductNotFound: Если продукт не найден.
        """
        logger.info(f"Retrieving product with pk={pk}")
        try:
            product = cls._apply_common_annotations(
                Product.objects.all()
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
            request: Any,
            source: Union[Any, Search],
            category_id: Optional[int] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            min_discount: Optional[float] = None,
            in_stock: Optional[bool] = None,
            my_products: Optional[QuerySet] = None,
    ) -> Union[Any, Search]:
        """Применяет общие фильтры к QuerySet или объекту поиска Elasticsearch.

        Args:
            request: request
            source: QuerySet (для PostgreSQL) или объект Search (для Elasticsearch).
            category_id: ID категории для фильтрации.
            min_price: Минимальная цена (с учётом скидки для Elasticsearch).
            max_price: Максимальная цена (с учётом скидки для Elasticsearch).
            min_discount: Минимальная скидка (в процентах).
            in_stock: Фильтр по наличию на складе.
            my_products: Фильтр продукта по пользователю

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
                # if my_products and request.user.is_authenticated:
                #     source = source.filter('terms', user_id=request.user.id)
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
                # if my_products and request.user.is_authenticated:
                #     source = source.filter(user_id=request.user.id)
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
        return cls.apply_common_filters(request, queryset, **params)

    @classmethod
    def apply_ordering(cls, queryset: Any, request: Any) -> Any:
        """Применяет сортировку к QuerySet или объекту поиска Elasticsearch на основе параметра запроса.

        Для поисковых запросов (q присутствует):
        - Если ordering не указан или недопустим, сохраняется порядок по _score (для Elasticsearch) или текущий порядок (для QuerySet).
        - Если ordering указан и допустим, применяется указанная сортировка.
        Для не-поисковых запросов:
        - Если ordering не указан или недопустим, применяется сортировка по -popularity_score.
        - Если ordering указан и допустим, применяется указанная сортировка.

        Args:
            queryset: QuerySet продуктов или объект Search для Elasticsearch.
            request: HTTP-запрос с параметром сортировки.

        Returns:
            Отсортированный QuerySet или объект Search.
        """
        sort_by = request.GET.get('ordering')
        is_search = bool(request.GET.get('q', '').strip())
        logger.debug(f"Applying ordering with sort_by={sort_by}, is_search={is_search}")

        if sort_by and sort_by not in cls.ALLOWED_ORDER_FIELDS:
            logger.warning(f"Invalid ordering field: {sort_by}")
            sort_by = None

        if isinstance(queryset, Search):
            if sort_by:
                logger.debug(f"Applying Elasticsearch sort: {sort_by}")
                return queryset.sort(sort_by)
            logger.debug("No valid sort_by for Elasticsearch search, preserving _score")
            return queryset  # Сохраняем _score
        else:
            if is_search:
                if sort_by:
                    logger.debug(f"Applying QuerySet sort for search: {sort_by}")
                    return queryset.order_by(sort_by)
                logger.debug("No valid sort_by for search QuerySet, preserving _score order")
                return queryset  # Сохраняем порядок _score через preserved_order
            else:
                if sort_by:
                    logger.debug(f"Applying QuerySet sort for non-search: {sort_by}")
                    return queryset.order_by(sort_by)
                logger.debug("No valid sort_by for non-search QuerySet, sorting by -popularity_score")
                return queryset.order_by('-popularity_score')

    @classmethod
    def search_products(cls, request: Any) -> Any:
        """Выполняет поиск продуктов через Elasticsearch и возвращает QuerySet, отсортированный по релевантности.

        Args:
            request: HTTP-запрос с параметром поиска q.

        Returns:
            QuerySet с результатами поиска, отсортированный по _score.

        Raises:
            ProductServiceException: При ошибках поиска.
        """
        try:
            query = request.GET.get('q', '').strip()
            if not query:
                logger.warning("Empty search query in search_products")
                return cls.get_base_queryset(request).none()

            search = ProductDocument.search()

            # Формируем поисковый запрос
            is_exact_search = query.startswith('"') and query.endswith('"')
            if is_exact_search:
                query = query[1:-1].strip()  # Убираем кавычки
                search = search.query(
                    'bool',
                    must=[
                        {'term': {'title.raw': {'value': query, 'boost': 10.0}}}
                    ]
                )
            else:
                search = search.query(
                    'bool',
                    must=[
                        {
                            'bool': {
                                'should': [
                                    # Точное совпадение с названием (высокий вес)
                                    {'term': {'title.raw': {'value': query, 'boost': 10.0}}},

                                    # Поиск по названию
                                    {'match': {
                                        'title': {
                                            'query': query,
                                            'boost': 5.0,
                                            'operator': 'and'
                                        }
                                    }},

                                    # Поиск по n-граммам в названии
                                    {'match': {
                                        'title.ngram': {
                                            'query': query,
                                            'boost': 3.0
                                        }
                                    }},

                                    # Поиск по описанию
                                    {'match': {
                                        'description': {
                                            'query': query,
                                            'boost': 1.0,
                                            'operator': 'and'
                                        }
                                    }}
                                ],
                                'minimum_should_match': 1
                            }
                        }
                    ]
                )

            # Сортировка по релевантности
            search = search.sort('_score')

            # Получаем ID продуктов из Elasticsearch
            search = search[:cls.LARGE_PAGE_SIZE]
            response = search.execute()

            # Логируем результаты и их _score
            logger.debug(f"Elasticsearch hits: {[(hit.meta.id, hit.meta.score) for hit in response]}")

            if not response.hits:
                return cls.get_base_queryset().none()

            # Получаем продукты из базы данных с сохранением порядка из Elasticsearch
            product_ids = [hit.meta.id for hit in response]
            logger.debug(f"Final product_ids order: {product_ids}")
            products = cls.get_base_queryset(request).filter(id__in=product_ids)

            # Сохраняем порядок сортировки из Elasticsearch
            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(product_ids)],
                output_field=IntegerField()
            )
            return products.order_by(preserved_order)

        except Exception as e:
            logger.error(f"Error in search_products: {str(e)}")
            raise ProductServiceException(f"Ошибка при поиске продуктов: {str(e)}")

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
            ).filter(search_vector=query)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise ProductServiceException(f"Ошибка поиска: {str(e)}")
