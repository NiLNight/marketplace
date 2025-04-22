# views.py
from django.contrib.postgres.search import SearchQuery, SearchRank
from mptt.utils import get_cached_trees

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from apps.products.models import Product, Category
from apps.products.services.product_services import ProductServices
from apps.products.services.query_services import ProductQueryService
from apps.products.permissions import IsOwnerOrAdmin
from apps.products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    CategorySerializer
)
from apps.products.exceptions import ProductServiceException
from apps.core.services.cache_services import CacheService


class CategoryListView(APIView):
    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        try:
            categories = Category.objects.prefetch_related('children').all()
            root_nodes = get_cached_trees(categories)
            serializer = CategorySerializer(root_nodes, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class ProductPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'


class BaseProductView(APIView):
    """
    Базовый класс для продуктовых view с общими настройками
    """
    pagination_class = ProductPagination
    CACHE_TIMEOUT = 60 * 15  # 15 минут


class ProductListView(BaseProductView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Получение списка продуктов с фильтрацией, сортировкой и пагинацией
        """
        try:
            cache_key = CacheService.build_cache_key(request, prefix="product_list")
            cached_data = CacheService.get_cached_data(cache_key)
            if cached_data:
                return Response(cached_data)

            # Базовый запрос без аннотаций
            base_queryset = ProductQueryService.get_base_queryset()
            # Поиск, если есть запрос
            if request.GET.get('q'):
                queryset = ProductQueryService.search_products(base_queryset, request)
            else:
                queryset = base_queryset

            # Применяем фильтры и сортировку
            queryset = ProductQueryService.apply_filters(queryset, request)

            # Добавляем аннотации перед сортировкой
            queryset = ProductQueryService.get_product_list(queryset)
            queryset = ProductQueryService.apply_ordering(queryset, request)

            # Пагинация
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)

            serializer = self.serializer_class(page, many=True)
            response_data = paginator.get_paginated_response(serializer.data).data
            CacheService.set_cached_data(cache_key, response_data, timeout=900)
            return Response(response_data)

        except ProductServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductCreateView(BaseProductView):
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Создание нового продукта
        """
        try:
            serializer = self.serializer_class(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            ProductServices.create_product(
                data=serializer.validated_data,
            )
            CacheService.invalidate_cache(prefix="product_list")
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        except DRFValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except ProductServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(BaseProductView):
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """
        Получение детальной информации о продукте
        """
        try:
            cached_data = CacheService.cache_product_details(pk)
            if cached_data:
                return Response(cached_data)

            product = ProductQueryService.get_single_product(pk)
            serializer = self.serializer_class(product)
            CacheService.set_cached_data(f'product_detail:{pk}', serializer.data, timeout=7200)
            return Response(serializer.data)

        except Product.DoesNotExist:
            raise NotFound("Товар не найден")
        except ProductServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(BaseProductView):
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def patch(self, request, pk):
        """
        Частичное обновление продукта
        """
        try:
            product = ProductQueryService.get_single_product(pk)
            self.check_object_permissions(request, product)

            serializer = self.serializer_class(
                product,
                data=request.data,
                context={'request': request},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            updated_product = ProductServices.update_product(
                product, serializer.validated_data
            )

            CacheService.invalidate_cache(prefix="product_detail", pk=product.id)
            CacheService.invalidate_cache(prefix="product_list")

            return Response(self.serializer_class(updated_product).data)

        except Product.DoesNotExist:
            raise NotFound("Товар не найден")
        except DRFValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except ProductServiceException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductDeleteView(BaseProductView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def delete(self, request, pk):
        """
        Мягкое удаление продукта
        """
        try:
            product = ProductQueryService.get_single_product(pk)
            self.check_object_permissions(request, product)

            ProductServices.delete_product(product)

            CacheService.invalidate_cache(prefix="product_detail", pk=product.id)
            CacheService.invalidate_cache(prefix="product_list")

            return Response("Товар удален", status=status.HTTP_204_NO_CONTENT)

        except Product.DoesNotExist:
            raise NotFound("Товар не найден")
        except ProductServiceException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
