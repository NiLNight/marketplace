from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from apps.reviews.models import Review, Comment
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


class ReviewListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get(self, request, product_id: int):
        """Получение списка отзывов для продукта."""
        cache_key = f'reviews_{product_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        reviews = Review.objects.filter(product_id=product_id)
        ordering = request.query_params.get('ordering')
        reviews = ReviewService.apply_ordering(reviews, ordering)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reviews, request)
        serializer = ReviewSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        cache.set(cache_key, response.data, timeout=300)  # Кэш на 5 минут
        return response


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def post(self, request):
        """Создание нового отзыва."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            review = ReviewService.create_review(serializer.validated_data, request.user)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def patch(self, request, pk: int):
        """Обновление отзыва."""
        review = get_object_or_404(Review, pk=pk)
        serializer = self.serializer_class(review, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_review = ReviewService.update_review(review, serializer.validated_data, request.user)
                return Response(ReviewSerializer(updated_review).data)
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentCreateSerializer

    def post(self, request):
        """Создание нового комментария."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            comment = CommentService.create_comment(serializer.validated_data, request.user)
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentCreateSerializer

    def patch(self, request, pk: int):
        """Обновление комментария."""
        comment = get_object_or_404(Comment, pk=pk)
        serializer = self.serializer_class(comment, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_comment = CommentService.update_comment(comment, serializer.validated_data, request.user)
                return Response(CommentSerializer(updated_comment).data)
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        """Переключение лайков для отзыва."""
        review = get_object_or_404(Review, pk=pk)
        result = LikeService.toggle_review_like(review, request.user)
        return Response(result)


class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        """Переключение лайков для комментария."""
        comment = get_object_or_404(Comment, pk=pk)
        result = LikeService.toggle_comment_like(comment, request.user)
        return Response(result)