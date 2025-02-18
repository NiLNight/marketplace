from django.db.models import Avg, Count, F, ExpressionWrapper, FloatField, Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.db.models.functions import Coalesce, ExtractDay, Now

from apps.products.models import Product, Category

from apps.products.serializers import ProductListSerializer


class ProductListView(APIView):
    serializer_class = ProductListSerializer

    def get_queryset(self):
        queryset = Product.objects.annotate(
            purchase_count=Count('order_items',
                                 filter=~Q(order_items__order=None),
                                 distinct=True),
            review_count=Count('ratings', distinct=True),
            rating_avg=Coalesce(Avg('ratings__value'), 0.0),
            days_since_created=ExtractDay(Now() - F('created')),
        )

        queryset = queryset.annotate(
            popularity_score=ExpressionWrapper(
                (F('purchase_count') * 0.4) +
                (F('review_count') * 0.2) +
                (F('rating_avg') * 0.3) +
                (1 / (F('days_since_created') + 1) * 0.1),
                output_field=FloatField()
            )
        )
        return queryset

    def get(self, request):
        queryset = self.get_queryset()

        # Фильтр по категории
        if category_id := request.query_params.get('category'):
            try:
                category = Category.objects.get(id=category_id)
                # Получаем всех потомков включая саму категорию
                descendants = category.get_descendants(include_self=True)
                # Преобразуем QuerySet в список ID
                category_ids = [c.id for c in descendants]
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                # Если категория не найдена - возвращаем пустой результат
                queryset = queryset.none()

        # Фильтр по цене
        price_params = {}
        if min_price := request.query_params.get('price__gte'):
            price_params['price__gte'] = min_price
        if max_price := request.query_params.get('price__lte'):
            price_params['price__lte'] = max_price
        queryset = queryset.filter(**price_params)

        # Если не указана сортировка - используем кастомный алгоритм
        sort_by = request.query_params.get('ordering')
        if not sort_by:
            queryset = queryset.order_by('-popularity_score')
        else:
            queryset = queryset.order_by(sort_by)

        # Пагинация через DRF
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
