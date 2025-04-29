import logging
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q, ExpressionWrapper, F, FloatField, Count, Avg, Prefetch
from django.db.models.functions import Coalesce, ExtractDay, Now
from apps.products.models import Product, Category
from apps.products.exceptions import ProductNotFound, InvalidCategoryError, ProductServiceException
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ProductQueryService:
    """Сервис для выполнения запросов к продуктам.

    Предоставляет методы для фильтрации, сортировки и поиска продуктов с аннотациями.
    """
    ALLOWED_ORDER_FIELDS = {
        '-popularity_score', 'price', '-price',
        '-created', 'rating_avg', '-rating_avg'
    }

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
            'discount', 'stock', 'is_active', 'category_id'
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
            logger.info(f"Successfully retrieved product {pk}")
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
        logger.debug("Applying common annotations to queryset")
        return queryset.annotate(
            rating_avg=Coalesce(Avg('reviews__value'), 0.0),
            purchase_count=Count(
                'order_items',
                filter=~Q(order_items__order=None),
                distinct=True
            ),
            review_count=Count('reviews', distinct=True),
            days_since_created=ExtractDay(Now() - F('created')),
            popularity_score=ExpressionWrapper(
                (F('purchase_count') * 0.4) +
                (F('review_count') * 0.2) +
                (F('rating_avg') * 0.3) +
                (1 / (F('days_since_created') + 1) * 0.1),
                output_field=FloatField()
            )
        )

    @classmethod
    def apply_filters(cls, queryset: Any, request: Any) -> Any:
        """Применяет фильтры к QuerySet на основе параметров запроса.

        Args:
            queryset: QuerySet продуктов.
            request: HTTP-запрос с параметрами фильтрации.

        Returns:
            Отфильтрованный QuerySet.

        Raises:
            InvalidCategoryError: Если категория или параметры цены некорректны.
        """
        params = request.GET.dict()
        logger.debug(f"Applying filters with params={params}")

        if category_id := params.get('category'):
            queryset = cls._filter_by_category(queryset, category_id)

        if any(key in params for key in ['price__gte', 'price__lte']):
            queryset = cls._filter_by_price(queryset, params)

        return queryset

    @staticmethod
    def _filter_by_category(queryset: Any, category_id: str) -> Any:
        """Фильтрует продукты по категории и ее потомкам.

        Args:
            queryset: QuerySet продуктов.
            category_id: Идентификатор категории.

        Returns:
            Отфильтрованный QuerySet.

        Raises:
            InvalidCategoryError: Если категория не существует.
        """
        logger.debug(f"Filtering by category_id={category_id}")
        try:
            category = Category.objects.get(pk=category_id)
            descendants = category.get_descendants(include_self=True)
            return queryset.filter(category__in=descendants)
        except Category.DoesNotExist:
            logger.warning(f"Category {category_id} not found")
            raise InvalidCategoryError("Категория не найдена.")

    @staticmethod
    def _filter_by_price(queryset: Any, params: Dict[str, str]) -> Any:
        """Фильтрует продукты по диапазону цен.

        Args:
            queryset: QuerySet продуктов.
            params: Параметры запроса с ценами.

        Returns:
            Отфильтрованный QuerySet.

        Raises:
            InvalidCategoryError: Если параметры цены некорректны.
        """
        logger.debug(f"Filtering by price with params={params}")
        try:
            price_filters = {}
            if min_price := params.get('price__gte'):
                price_filters['price__gte'] = float(min_price)
            if max_price := params.get('price__lte'):
                price_filters['price__lte'] = float(max_price)
            return queryset.filter(**price_filters)
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid price parameters: {str(e)}")
            raise InvalidCategoryError(f"Некорректные параметры цены: {str(e)}")

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

        return queryset.order_by(sort_by or 'popularity_score')

    @staticmethod
    def search_products(queryset: Any, request: Any) -> Any:
        """Выполняет поиск продуктов по текстовому запросу.

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
