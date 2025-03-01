from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.products.services.query_services import ProductQueryService
from apps.products.services.product_services import ProductServices
from apps.products.services.cache_services import CacheServices
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from apps.products.permissions import IsOwnerOrAdmin

from apps.products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer
)


class ProductPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class ProductListView(APIView):
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination

    CACHE_TIMEOUT = 60 * 15

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def get(self, request):
        cache_key = CacheServices.build_cache_key(request)
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response
        queryset = ProductQueryService.get_optimized_queryset()
        queryset = ProductQueryService.apply_filters(queryset, request)
        queryset = ProductQueryService.apply_ordering(queryset, request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        # cache.set(cache_key, response, self.CACHE_TIMEOUT)
        return response


class ProductCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        ProductServices.create_product(
            data=serializer.validated_data,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer

    def get(self, request, pk):
        try:
            product = ProductQueryService.get_optimized_queryset(pk=pk)
            serializer = self.serializer_class(product)
            return Response(serializer.data)
        except Exception:
            raise NotFound("Товар не найден")


class ProductUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = ProductDetailSerializer

    def patch(self, request, pk):
        product = ProductQueryService.get_optimized_queryset(pk=pk)
        self.check_object_permissions(request, product)
        serializer = self.serializer_class(
            product, data=request.data, context={'request': request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProductDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def delete(self, request, pk):
        try:
            ProductServices.delete_product(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response('Товар удален или не существует', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
