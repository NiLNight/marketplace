# query_services.py (обновленная версия)
from django.db.models import Q, ExpressionWrapper, F, FloatField, Count, Avg
from django.db.models.functions import Coalesce, ExtractDay, Now
from apps.products.models import Product, Category
from apps.products.exceptions import ProductNotFound, InvalidCategoryError  # 🚀 Добавлены кастомные исключения


class ProductQueryService:
    ALLOWED_ORDER_FIELDS = {
        'popularity_score', 'price', '-price',
        '-created', 'rating_avg', '-rating_avg'
    }

    # 🚀 Переименован метод для ясности
    @classmethod
    def get_base_queryset(cls):
        return Product.objects.filter(is_active=True)

    # 🚀 Разделен на два метода для единичного и списка продуктов
    @classmethod
    def get_product_list(cls):
        return cls._apply_common_annotations(
            cls.get_base_queryset()
        ).select_related('category').only(
            'title', 'price', 'thumbnail', 'created',
            'discount', 'stock', 'category__title',
            'category__slug', 'is_active'
        )

    @classmethod
    def get_single_product(cls, pk):
        try:
            return cls._apply_common_annotations(
                cls.get_base_queryset()
            ).get(pk=pk)
        except Product.DoesNotExist:
            raise ProductNotFound()  # 🚀 Кастомное исключение

    # 🚀 Вынесена общая логика аннотаций
    @staticmethod
    def _apply_common_annotations(queryset):
        return queryset.annotate(
            rating_avg=Coalesce(Avg('ratings__value'), 0.0),
            purchase_count=Count(
                'order_items',
                filter=~Q(order_items__order=None),
                distinct=True
            ),
            review_count=Count('ratings', distinct=True),
            days_since_created=ExtractDay(Now() - F('created')),
            popularity_score=ExpressionWrapper(  # 🚀 Перенесено из apply_ordering
                (F('purchase_count') * 0.4) +
                (F('review_count') * 0.2) +
                (F('rating_avg') * 0.3) +
                (1 / (F('days_since_created') + 1) * 0.1),
                output_field=FloatField()
            )
        )

    @classmethod
    def apply_filters(cls, queryset, request):
        """
        🚀 Добавлены:
        - Валидация параметров
        - Разделение на приватные методы
        - Кастомные исключения
        """
        params = request.GET.dict()

        # Фильтр по категории
        if category_id := params.get('category'):
            queryset = cls._filter_by_category(queryset, category_id)

        # Фильтр по цене
        if any(key in params for key in ['price__gte', 'price__lte']):
            queryset = cls._filter_by_price(queryset, params)

        return queryset

    @staticmethod
    def _filter_by_category(queryset, category_id):
        try:
            category = Category.objects.get(pk=category_id)
            descendants = category.get_descendants(include_self=True)
            return queryset.filter(category__in=descendants)
        except Category.DoesNotExist:
            raise InvalidCategoryError()  # 🚀 Замена на кастомное исключение

    @staticmethod
    def _filter_by_price(queryset, params):
        try:
            price_filters = {}
            if min_price := params.get('price__gte'):
                price_filters['price__gte'] = float(min_price)
            if max_price := params.get('price__lte'):
                price_filters['price__lte'] = float(max_price)
            return queryset.filter(**price_filters)
        except (TypeError, ValueError) as e:
            raise InvalidCategoryError(f"Некорректные параметры цены: {str(e)}")

    @classmethod
    def apply_ordering(cls, queryset, request):
        """
        🚀 Улучшения:
        - Валидация параметров сортировки
        - Безопасная обработка входных данных
        - Дефолтная сортировка по popularity_score
        """
        sort_by = request.GET.get('ordering')

        if sort_by and sort_by not in cls.ALLOWED_ORDER_FIELDS:
            sort_by = None  # 🚀 Игнорируем некорректные значения

        return queryset.order_by(sort_by or 'popularity_score')