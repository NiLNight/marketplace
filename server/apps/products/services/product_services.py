import hashlib

from django.db.models import Avg, Count, F, Q, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce, ExtractDay, Now

from apps.products.models import Product, Category


def build_cache_key(request):
    params = [
        f"{key}={value}"
        for key, value in sorted(request.GET.items())
        if key != 'page'
    ]

    # Создаем хеш из параметров
    params_str = "&".join(params)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()

    return f"product_list:{params_hash}"


def get_optimized_queryset():
    return Product.objects.active().annotate(
        rating_avg=Coalesce(Avg('ratings__value'), 0.0),
        purchase_count=Count('order_items',
                             filter=~Q(order_items__order=None), distinct=True),
        review_count=Count('ratings', distinct=True),
        days_since_created=ExtractDay(Now() - F('created')),
    ).select_related('category').only(
        'title', 'price', 'thumbnail', 'created',
        'discount', 'stock', 'category__title', 'category__slug', 'is_active'
    )


def apply_filters(queryset, request):
    # Фильтр по категории
    if category_id := request.GET.get('category'):
        try:
            category = Category.objects.get(pk=category_id)
            descendants = category.get_descendants(include_self=True)
            queryset = queryset.filter(category__in=descendants)
        except Category.DoesNotExist:
            queryset = queryset.none()

    # Фильтр по цене
    try:
        price_params = {}
        if min_price := request.GET.get('price__gte'):
            price_params['price__gte'] = float(min_price)
        if max_price := request.GET.get('price__lte'):
            price_params['price__lte'] = float(max_price)
        queryset = queryset.filter(**price_params)
    except (TypeError, ValueError):
        pass

    return queryset


def apply_ordering(queryset, request):
    allowed_order_fields = {
        'popularity_score', 'price', '-price',
        '-created', 'rating_avg', '-rating_avg',
    }
    # Сортировка
    sort_by = request.GET.get('ordering')
    queryset = queryset.annotate(
        popularity_score=ExpressionWrapper(
            (F('purchase_count') * 0.4) +
            (F('review_count') * 0.2) +
            (F('rating_avg') * 0.3) +
            (1 / (F('days_since_created') + 1) * 0.1),
            output_field=FloatField()
        )
    ).order_by('popularity_score')

    if sort_by and sort_by in allowed_order_fields:
        return queryset.order_by(sort_by)
    return queryset
