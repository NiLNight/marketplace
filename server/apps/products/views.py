import logging
from django.contrib.postgres.search import SearchQuery, SearchRank
from mptt.utils import get_cached_trees
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from apps.products.exceptions import ProductServiceException, InvalidProductData, ProductNotFound
from apps.products.models import Category
from apps.products.services.product_services import ProductServices
from apps.products.services.query_services import ProductQueryService
from apps.products.permissions import IsOwnerOrAdmin
from apps.products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    CategorySerializer
)
from apps.products.utils import handle_api_errors
from apps.core.services.cache_services import CacheService
from typing import Any

logger = logging.getLogger(__name__)


class ProductPagination(PageNumberPagination):
    """Настройки пагинации для списков продуктов."""
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


class BaseProductView(APIView):
    """Базовый класс для представлений продуктов."""
    pagination_class = ProductPagination
    CACHE_TIMEOUT = 60 * 15  # 15 минут


class CategoryListView(BaseProductView):
    """Представление для получения списка категорий."""
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 60))
    @handle_api_errors
    def get(self, request: Any) -> Response:
        """Обрабатывает GET-запрос для получения иерархического списка категорий.

        Args:
            request: HTTP-запрос.

        Returns:
            Response с данными категорий.

        Raises:
            ProductServiceException: Если получение категорий не удалось.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving categories, user={user_id}, path={request.path}")
        try:
            categories = Category.objects.prefetch_related('children').all()
            root_nodes = get_cached_trees(categories)
            serializer = CategorySerializer(root_nodes, many=True)
            logger.info(f"Successfully retrieved {len(root_nodes)} categories, user={user_id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to retrieve categories: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка получения категорий: {str(e)}")


class ProductListView(BaseProductView):
    """Представление для получения списка продуктов."""
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    @handle_api_errors
    def get(self, request: Any) -> Response:
        """Обрабатывает GET-запрос для получения пагинированного списка продуктов.

        Args:
            request: HTTP-запрос с параметрами фильтрации и сортировки.

        Returns:
            Response с пагинированным списком продуктов.

        Raises:
            ProductServiceException: Если запрос некорректен или обработка не удалась.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving product list, user={user_id}, path={request.path}")
        try:
            cache_key = CacheService.build_cache_key(request, prefix="product_list")
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                return Response(cached_data)

            base_queryset = ProductQueryService.get_base_queryset()
            if request.GET.get('q'):
                queryset = ProductQueryService.search_products(base_queryset, request)
            else:
                queryset = base_queryset

            queryset = ProductQueryService.apply_filters(queryset, request)
            queryset = ProductQueryService.get_product_list(queryset)
            queryset = ProductQueryService.apply_ordering(queryset, request)

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(page, many=True)

            response_data = paginator.get_paginated_response(serializer.data).data
            CacheService.set_cached_data(cache_key, response_data, timeout=self.CACHE_TIMEOUT)
            logger.info(f"Retrieved {len(page)} products, user={user_id}")
            return Response(response_data)
        except Exception as e:
            logger.error(f"Failed to retrieve product list: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка получения списка продуктов: {str(e)}")


class ProductCreateView(BaseProductView):
    """Представление для создания нового продукта."""
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request: Any) -> Response:
        """Обрабатывает POST-запрос для создания продукта.

        Args:
            request: HTTP-запрос с данными продукта.

        Returns:
            Response с данными созданного продукта.

        Raises:
            InvalidProductData: Если данные некорректны.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Creating product, user={user_id}, path={request.path}")
        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            product = ProductServices.create_product(serializer.validated_data, request.user)
            CacheService.invalidate_cache(prefix="product_list")
            logger.info(f"Successfully created product {product.id}, user={user_id}")
            return Response(
                ProductDetailSerializer(product).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Failed to create product: {str(e)}, user={user_id}")
            raise InvalidProductData(f"Ошибка создания продукта: {str(e)}")


class ProductDetailView(BaseProductView):
    """Представление для получения детальной информации о продукте."""
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    @handle_api_errors
    def get(self, request: Any, pk: int) -> Response:
        """Обрабатывает GET-запрос для получения информации о продукте.

        Args:
            request: HTTP-запрос.
            pk: Идентификатор продукта.

        Returns:
            Response с данными продукта.

        Raises:
            ProductNotFound: Если продукт не найден.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving product {pk}, user={user_id}, path={request.path}")
        try:
            cache_key = f'product_detail:{pk}'
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                return Response(cached_data)

            product = ProductQueryService.get_single_product(pk)
            serializer = self.serializer_class(product)
            CacheService.set_cached_data(cache_key, serializer.data, timeout=7200)
            logger.info(f"Successfully retrieved product {pk}, user={user_id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to retrieve product {pk}: {str(e)}, user={user_id}")
            raise ProductNotFound(f"Ошибка получения продукта: {str(e)}")


class ProductUpdateView(BaseProductView):
    """Представление для обновления продукта."""
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @handle_api_errors
    def patch(self, request: Any, pk: int) -> Response:
        """Обрабатывает PATCH-запрос для частичного обновления продукта.

        Args:
            request: HTTP-запрос с данными.
            pk: Идентификатор продукта.

        Returns:
            Response с данными обновленного продукта.

        Raises:
            ProductNotFound: Если продукт не найден.
            InvalidProductData: Если данные некорректны.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Updating product {pk}, user={user_id}, path={request.path}")
        try:
            product = ProductQueryService.get_single_product(pk)
            self.check_object_permissions(request, product)

            serializer = self.serializer_class(
                product, data=request.data, context={'request': request}, partial=True
            )
            serializer.is_valid(raise_exception=True)
            updated_product = ProductServices.update_product(product, serializer.validated_data, request.user)

            CacheService.invalidate_cache(prefix="product_detail", pk=product.id)
            CacheService.invalidate_cache(prefix="product_list")
            logger.info(f"Successfully updated product {pk}, user={user_id}")
            return Response(self.serializer_class(updated_product).data)
        except Exception as e:
            logger.error(f"Failed to update product {pk}: {str(e)}, user={user_id}")
            raise InvalidProductData(f"Ошибка обновления продукта: {str(e)}")


class ProductDeleteView(BaseProductView):
    """Представление для удаления продукта."""
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @handle_api_errors
    def delete(self, request: Any, pk: int) -> Response:
        """Обрабатывает DELETE-запрос для мягкого удаления продукта.

        Args:
            request: HTTP-запрос.
            pk: Идентификатор продукта.

        Returns:
            Response с подтверждением удаления.

        Raises:
            ProductNotFound: Если продукт не найден.
            ProductServiceException: Если удаление не удалось.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Deleting product {pk}, user={user_id}, path={request.path}")
        try:
            product = ProductQueryService.get_single_product(pk)
            self.check_object_permissions(request, product)

            ProductServices.delete_product(product, request.user)
            CacheService.invalidate_cache(prefix="product_detail", pk=product.id)
            CacheService.invalidate_cache(prefix="product_list")
            logger.info(f"Successfully deleted product {pk}, user={user_id}")
            return Response({"message": "Продукт удален"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Failed to delete product {pk}: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка удаления продукта: {str(e)}")
