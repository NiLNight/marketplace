from django.core.paginator import Paginator
from django.db.models import Avg
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product, Category

from apps.products.serializers import ProductListSerializer


class ProductListView(APIView):
    serializer_class = ProductListSerializer

    def get(self, request):
        # Фильтрация и аннотации
        queryset = Product.objects.active().select_related('category')
        queryset = queryset.annotate(rating_avg=Avg('ratings__value'))

        # Фильтр по категории
        if category_id := request.query_params.get('category'):
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

        # Сортировка
        sort_by = request.query_params.get('ordering', '-created')
        queryset = queryset.order_by(sort_by)

        # Пагинация через DRF
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
