from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from apps.reviews.models import Review, Comment, ReviewLike, CommentLike
from apps.reviews.services.reviews_services import ReviewService
from apps.reviews.services.comment_services import CommentService
from apps.reviews.services.like_services import LikeService
from apps.reviews.serializers import (
    ReviewCreateSerializer,
    ReviewSerializer,
    CommentSerializer,
    CommentCreateSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None
    service_class = None
    create_method = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            create_func = getattr(self.service_class, self.create_method)
            instance = create_func(serializer.validated_data, request.user)
            return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None
    service_class = None
    model_class = None
    update_method = None  # Метод сервиса для обновления, будет переопределяться

    def patch(self, request, pk: int):
        instance = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                # Вызываем метод обновления, определенный в дочернем классе
                update_func = getattr(self.service_class, self.update_method)
                updated_instance = update_func(
                    instance, serializer.validated_data, request.user
                )
                return Response(self.serializer_class(updated_instance).data, status=status.HTTP_200_OK)
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get(self, request, product_id: int):
        """Получение списка отзывов для продукта."""
        cache_key = f'reviews_{product_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        reviews = Review.objects.filter(product_id=product_id).prefetch_related('likes__user__reviews', 'user')
        ordering = request.query_params.get('ordering')
        reviews = ReviewService.apply_ordering(reviews, ordering)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reviews, request)
        serializer = ReviewSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, timeout=300)  # Кэш на 5 минут
        return response


class ReviewCreateView(BaseCreateView):
    serializer_class = ReviewCreateSerializer
    service_class = ReviewService
    create_method = 'create_review'


class ReviewUpdateView(BaseUpdateView):
    serializer_class = ReviewCreateSerializer
    service_class = ReviewService
    model_class = Review
    update_method = 'update_review'


class CommentListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get(self, request, review_id: int):
        """Получение списка комментариев для отзыва."""
        cache_key = f'comments_{review_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        comments = Comment.objects.filter(review_id=review_id, parent=None)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(comments, request)
        serializer = CommentSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, timeout=300)
        return response


class CommentCreateView(BaseCreateView):
    serializer_class = CommentCreateSerializer
    service_class = CommentService
    create_method = 'create_comment'


class CommentUpdateView(BaseUpdateView):
    serializer_class = CommentCreateSerializer
    service_class = CommentService
    model_class = Comment
    update_method = 'update_comment'


class ReviewLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        """Переключение лайков для отзыва."""
        review = get_object_or_404(Review, pk=pk)
        result = LikeService.toggle_like(ReviewLike, review, request.user, 'reviews')
        return Response(result)


class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        """Переключение лайков для комментария."""
        comment = get_object_or_404(Comment, pk=pk)
        result = LikeService.toggle_like(CommentLike, comment, request.user, 'comments')
        return Response(result)
