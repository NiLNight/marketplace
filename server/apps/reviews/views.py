import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.core.services.cache_services import CacheService
from apps.core.services.like_services import LikeService
from apps.reviews.models import Review
from apps.reviews.services.reviews_services import ReviewService
from apps.reviews.serializers import ReviewSerializer, ReviewCreateSerializer
from apps.comments.utils import handle_api_errors
from django.contrib.contenttypes.models import ContentType


logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Настройки пагинации для списков отзывов.

    Определяет размер страницы и параметры запроса для пагинированных ответов.

    Атрибуты:
        page_size (int): Количество элементов на странице по умолчанию.
        page_size_query_param (str): Параметр запроса для изменения размера страницы.
        max_page_size (int): Максимально допустимый размер страницы.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReviewListView(APIView):
    """Представление для получения списка отзывов о продукте."""
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    serializer_class = ReviewSerializer

    @handle_api_errors
    def get(self, request, product_id: int):
        """Обрабатывает GET-запросы для получения пагинированного списка отзывов.

        Args:
            request (HttpRequest): Входящий объект запроса.
            product_id (int): ID продукта для получения отзывов.

        Returns:
            Response: Пагинированный список отзывов или ответ с ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving reviews for product={product_id}, user={user_id}")

        # Проверка кэша на наличие данных отзывов
        cache_key = CacheService.build_cache_key(request, prefix=f"reviews:{product_id}")
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            return Response(cached_data)

        # Получение и пагинация отзывов
        reviews = ReviewService.get_reviews(product_id)
        ordering = request.query_params.get('ordering')
        reviews = ReviewService.apply_ordering(reviews, ordering)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reviews, request)
        serializer = self.serializer_class(page, many=True)

        # Кэширование пагинированного ответа
        response_data = paginator.get_paginated_response(serializer.data).data
        CacheService.set_cached_data(cache_key, response_data, timeout=300)
        logger.info(f"Retrieved {len(reviews)} reviews for product={product_id}, user={user_id}")
        return Response(response_data)


class ReviewCreateView(APIView):
    """Представление для создания нового отзыва."""
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запросы для создания нового отзыва.

        Args:
            request (HttpRequest): Входящий объект запроса с данными отзыва.

        Returns:
            Response: Данные созданного отзыва или ответ с ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Creating review by user={user_id}, path={request.path}")

        # Проверка входящих данных
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создание отзыва и инвалидация кэша
        review = ReviewService.create_review(serializer.validated_data, request.user)
        CacheService.invalidate_cache(prefix=f"reviews:{review.product_id}")
        CacheService.invalidate_cache(prefix=f"comments:{review.id}")
        logger.info(f"Created Review {review.id}, user={user_id}")
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewUpdateView(APIView):
    """Представление для обновления существующего отзыва."""
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    @handle_api_errors
    def patch(self, request, pk: int):
        """Обрабатывает PATCH-запросы для обновления отзыва.

        Args:
            request (HttpRequest): Входящий объект запроса с обновленными данными.
            pk (int): ID отзыва для обновления.

        Returns:
            Response: Данные обновленного отзыва или ответ с ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Updating Review {pk}, user={user_id}, path={request.path}")

        # Проверка входящих данных
        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Обновление отзыва и инвалидация кэша
        updated_review = ReviewService.update_review(pk, serializer.validated_data, request.user)
        CacheService.invalidate_cache(prefix=f"reviews:{updated_review.product_id}")
        CacheService.invalidate_cache(prefix=f"comments:{updated_review.id}")
        logger.info(f"Updated Review {pk}, user={user_id}")
        return Response(ReviewSerializer(updated_review).data, status=status.HTTP_200_OK)


class ReviewLikeView(APIView):
    """Представление для управления лайками отзывов."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk: int):
        """Обрабатывает POST-запросы для переключения лайка отзыва.

        Args:
            request (HttpRequest): Входящий объект запроса.
            pk (int): ID отзыва для лайка или снятия лайка.

        Returns:
            Response: Результат операции с лайком или ответ с ошибкой.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Toggling like for review={pk}, user={user_id}, path={request.path}")

        # Использование общего сервиса LikeService
        content_type = ContentType.objects.get_for_model(Review)
        result = LikeService.toggle_like(content_type, pk, request.user)
        CacheService.invalidate_cache(prefix=f"reviews")
        logger.info(f"Like toggled for review={pk}: {result['action']}, user={user_id}")
        return Response(result, status=status.HTTP_200_OK)
