import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.core.services.cache_services import CacheService
from apps.reviews.models import Review
from apps.reviews.services.reviews_services import ReviewService
from apps.reviews.services.like_services import LikeService
from apps.reviews.serializers import ReviewCreateSerializer, ReviewSerializer
from apps.reviews.utils import handle_api_errors
from apps.reviews.exceptions import ReviewNotFound, ReviewException

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Пагинация для списков."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReviewListView(APIView):
    """Получение списка отзывов о продукте."""
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    @handle_api_errors
    def get(self, request, product_id: int):
        """Обрабатывает GET-запрос для списка отзывов.

        Args:
            request: Объект запроса.
            product_id (int): ID продукта.

        Returns:
            Response: Пагинированный список отзывов или ошибка.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Retrieving reviews for product={product_id}, user={user_id}")
        cache_key = CacheService.build_cache_key(request, prefix=f"reviews:{product_id}")
        cached_data = CacheService.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for reviews of product={product_id}, user={user_id}")
            return Response(cached_data)

        try:
            reviews = Review.objects.filter(product_id=product_id).prefetch_related('likes', 'user')
            ordering = request.query_params.get('ordering')
            reviews = ReviewService.apply_ordering(reviews, ordering)

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(reviews, request)
            serializer = ReviewSerializer(page, many=True)
            response_data = paginator.get_paginated_response(serializer.data).data

            CacheService.set_cached_data(cache_key, response_data, timeout=300)
            logger.info(f"Retrieved {len(reviews)} reviews for product={product_id}, user={user_id}")
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error retrieving reviews for product={product_id}: {str(e)}, user={user_id}")
            return Response(
                {"error": "Внутренняя ошибка сервера", "code": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReviewCreateView(APIView):
    """Создание нового отзыва."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для создания отзыва.

        Args:
            request: Объект запроса.

        Returns:
            Response: Данные созданного отзыва или ошибка.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Creating review by user={user_id}")
        serializer = ReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                review = ReviewService.create_review(serializer.validated_data, request.user)
                CacheService.invalidate_cache(prefix=f"reviews:{review.product_id}")
                logger.info(f"Created Review {review.id}, user={user_id}")
                return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating review: {str(e)}, user={user_id}")
                return Response({"error": str(e), "code": "create_error"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"Invalid data for review creation: {serializer.errors}, user={user_id}")
        return Response({"error": serializer.errors, "code": "validation_error"}, status=status.HTTP_400_BAD_REQUEST)


class ReviewUpdateView(APIView):
    """Обновление существующего отзыва."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def patch(self, request, pk: int):
        """Обрабатывает PATCH-запрос для обновления отзыва.

        Args:
            request: Объект запроса.
            pk (int): ID отзыва.

        Returns:
            Response: Обновленные данные или ошибка.

        Raises:
            ReviewNotFound: Если отзыв не найден.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Updating Review {pk}, user={user_id}")
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            logger.warning(f"Review {pk} not found, user={user_id}")
            raise ReviewNotFound()
        serializer = ReviewCreateSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_review = ReviewService.update_review(review, serializer.validated_data, request.user)
                CacheService.invalidate_cache(prefix=f"reviews:{updated_review.product_id}")
                logger.info(f"Updated Review {pk}, user={user_id}")
                return Response(ReviewSerializer(updated_review).data, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error updating Review {pk}: {str(e)}, user={user_id}")
                return Response({"error": str(e), "code": "update_error"}, status=status.HTTP_400_BAD_REQUEST)
        logger.warning(f"Invalid data for Review {pk}: {serializer.errors}, user={user_id}")
        return Response({"error": serializer.errors, "code": "validation_error"}, status=status.HTTP_400_BAD_REQUEST)


class ReviewLikeView(APIView):
    """Управление лайками для отзывов."""
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk: int):
        """Обрабатывает POST-запрос для переключения лайка отзыва.

        Args:
            request: Объект запроса.
            pk (int): ID отзыва.

        Returns:
            Response: Результат операции или ошибка.

        Raises:
            ReviewNotFound: Если отзыв не найден.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Toggling like for review={pk}, user={user_id}")
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            logger.warning(f"Review {pk} not found, user={user_id}")
            raise ReviewNotFound()
        try:
            result = LikeService.toggle_like(review, request.user)
            logger.info(f"Like toggled for review={pk}: {result['action']}, user={user_id}")
            return Response(result)
        except ReviewException as e:
            logger.error(f"Error toggling like for review={pk}: {str(e)}, user={user_id}")
            return Response({"error": str(e), "code": e.__class__.__name__.lower()}, status=e.status_code)
