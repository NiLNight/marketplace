import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.reviews.exceptions import LikeOperationFailed, ReviewNotFound
from apps.core.services.cache_services import CacheService
from apps.core.services.like_services import LikeService
from apps.reviews.models import Review
from apps.reviews.services.reviews_services import ReviewService
from apps.reviews.serializers import ReviewSerializer, ReviewCreateSerializer
from apps.reviews.utils import handle_api_errors
from django.contrib.contenttypes.models import ContentType
from apps.products.services.tasks import update_popularity_score

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Настройки пагинации для списков отзывов.

    Attributes:
        page_size: Количество элементов на странице (по умолчанию 10).
        page_size_query_param: Параметр запроса для размера страницы.
        max_page_size: Максимальный размер страницы (100).
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReviewListView(APIView):
    """Представление для получения списка отзывов о продукте.

    Attributes:
        permission_classes: Классы разрешений для доступа (чтение для всех, запись для аутентифицированных).
        pagination_class: Класс пагинации для списков отзывов.
        serializer_class: Класс сериализатора для преобразования данных отзывов.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    serializer_class = ReviewSerializer

    @handle_api_errors
    def get(self, request, product_id: int):
        """Обрабатывает GET-запрос для получения пагинированного списка отзывов о продукте.

        Args:
            request: HTTP-запрос с параметрами пагинации и сортировки.
            product_id: Идентификатор продукта, для которого запрашиваются отзывы.

        Returns:
            Response: Пагинированный список отзывов в формате JSON.

        Raises:
            Exception: Если получение списка отзывов не удалось (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Fetching reviews for product={product_id}, user={user_id}, path={request.path}")

        cached_data = CacheService.cache_review_list(product_id, request)
        if cached_data:
            return Response(cached_data)

        reviews = ReviewService.get_reviews(product_id)
        ordering = request.query_params.get('ordering')
        reviews = ReviewService.apply_ordering(reviews, ordering)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reviews, request)
        serializer = self.serializer_class(page, many=True)

        cache_key = CacheService.build_cache_key(request, prefix=f"reviews:{product_id}")
        response_data = paginator.get_paginated_response(serializer.data).data
        CacheService.set_cached_data(cache_key, response_data, timeout=300)
        logger.info(f"Retrieved {len(reviews)} reviews for product={product_id}, user={user_id}")
        return Response(response_data)


class ReviewCreateView(APIView):
    """Представление для создания нового отзыва.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных пользователей).
        serializer_class: Класс сериализатора для создания отзывов.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    @handle_api_errors
    def post(self, request):
        """Обрабатывает POST-запрос для создания отзыва.

        Args:
            request: HTTP-запрос с данными отзыва (продукт, оценка, текст, изображение).

        Returns:
            Response: Данные созданного отзыва в формате JSON с кодом статуса 201.

        Raises:
            Exception: Если создание отзыва не удалось из-за некорректных данных или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Creating review, user={user_id}, path={request.path}")

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.create_review(serializer.validated_data, request.user)
        logger.info(f"Created review {review.id}, user={user_id}")
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewUpdateView(APIView):
    """Представление для обновления отзыва.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных пользователей).
        serializer_class: Класс сериализатора для обновления отзывов.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    @handle_api_errors
    def patch(self, request, pk: int):
        """Обрабатывает PATCH-запрос для частичного обновления отзыва.

        Args:
            request: HTTP-запрос с данными для обновления (оценка, текст, изображение).
            pk: Идентификатор отзыва, который нужно обновить.

        Returns:
            Response: Данные обновленного отзыва в формате JSON с кодом статуса 200.

        Raises:
            Exception: Если обновление отзыва не удалось из-за некорректных данных, отсутствия прав или других ошибок (обрабатывается декоратором handle_api_errors).
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Updating review {pk}, user={user_id}, path={request.path}")

        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.update_review(pk, serializer.validated_data, request.user)
        logger.info(f"Updated review {pk}, user={user_id}")
        return Response(ReviewSerializer(review).data, status=status.HTTP_200_OK)


class ReviewLikeView(APIView):
    """Представление для управления лайками отзывов.

    Attributes:
        permission_classes: Классы разрешений для доступа (только для аутентифицированных пользователей).
    """
    permission_classes = [IsAuthenticated]

    @handle_api_errors
    def post(self, request, pk: int):
        """Обрабатывает POST-запрос для переключения лайка отзыва (добавить/удалить).

        Args:
            request: HTTP-запрос с информацией о пользователе.
            pk: Идентификатор отзыва, для которого переключается лайк.

        Returns:
            Response: Результат операции с лайком (действие и текущее количество лайков) в формате JSON с кодом статуса 200.

        Raises:
            LikeOperationFailed: Если операция с лайком не удалась из-за ошибки базы данных или других проблем.
        """
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.info(f"Toggling like for review={pk}, user={user_id}, path={request.path}")

        content_type = ContentType.objects.get_for_model(Review)
        try:
            review = Review.objects.get(pk=pk)
            result = LikeService.toggle_like(content_type, pk, request.user)
            CacheService.invalidate_cache(prefix=f"reviews:{review.product_id}")
            logger.info(f"Like toggled for review={pk}: {result['action']}, user={user_id}")
            return Response(result, status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            logger.error(f"Review {pk} not found, user={user_id}")
            raise ReviewNotFound(f"Отзыв с ID {pk} не найден.")
        except Exception as e:
            logger.error(f"Failed to toggle like for review={pk}: {str(e)}, user={user_id}")
            raise LikeOperationFailed(f"Ошибка при обработке лайка: {str(e)}")
