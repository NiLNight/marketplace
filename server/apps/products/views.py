import hashlib
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, ExpressionWrapper, FloatField
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db.models.functions import Coalesce, ExtractDay, Now

from apps.products.models import Product, Category
from apps.products.serializers import ProductListSerializer


class ProductPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class ProductListView(APIView):
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination

    ALLOWED_ORDER_FIELDS = {
        'popularity_score', 'price',
        '-created', 'rating_avg'
    }

    CACHE_TIMEOUT = 60 * 15

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def get(self, request):
        cache_key = self._build_cache_key(request)
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response
        queryset = self._get_optimized_queryset()
        queryset = self._apply_filters(queryset, request)
        queryset = self._apply_ordering(queryset, request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        # cache.set(cache_key, response, self.CACHE_TIMEOUT)
        return response

    def _build_cache_key(self, request):
        params = [
            f"{key}={value}"
            for key, value in sorted(request.GET.items())
            if key != 'page'
        ]

        # Создаем хеш из параметров
        params_str = "&".join(params)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        return f"product_list:{params_hash}"

    def _get_optimized_queryset(self):
        return Product.objects.active().annotate(
            rating_avg=Coalesce(Avg('ratings__value'), 0.0),
            purchase_count=Count('order_items',
                                 filter=~Q(order_items__order=None), distinct=True),
            review_count=Count('ratings', distinct=True),
            days_since_created=ExtractDay(Now() - F('created')),
        ).select_related('category').only(
            'title', 'price', 'thumbnail', 'created',
            'discount', 'category__title', 'is_active'
        )

    def _apply_filters(self, queryset, request):

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

    def _apply_ordering(self, queryset, request):
        # Сортировка
        sort_by = request.GET.get('ordering')
        if sort_by and sort_by.lstrip('-') not in self.ALLOWED_ORDER_FIELDS:
            return queryset.order_by(sort_by)
        return queryset.annotate(
            popularity_score=ExpressionWrapper(
                (F('purchase_count') * 0.4) +
                (F('review_count') * 0.2) +
                (F('rating_avg') * 0.3) +
                (1 / (F('days_since_created') + 1) * 0.1),
                output_field=FloatField()
            )
        ).order_by('-popularity_score')
