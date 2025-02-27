from apps.services.products import services
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from apps.products.serializers import ProductListSerializer


class ProductPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class ProductListView(APIView):
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination

    CACHE_TIMEOUT = 60 * 15

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def get(self, request):
        cache_key = services.build_cache_key(request)
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response
        queryset = services.get_optimized_queryset()
        queryset = services.apply_filters(queryset, request)
        queryset = services.apply_ordering(queryset, request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        # cache.set(cache_key, response, self.CACHE_TIMEOUT)
        return response
