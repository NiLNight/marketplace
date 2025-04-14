from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reviews.models import Review, Comment
from apps.reviews.services import reviews_services

from apps.reviews.serializers import (
    ReviewCreateSerializer,
    ReviewSerializer,
    CommentSerializer,
    CommentCreateSerializer
)
from apps.reviews.services import comment_services
from apps.reviews.services import like_services


class ReviewListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewSerializer

    def get(self, request, product_id: int):
        """Получение списка отзывов для продукта."""
        reviews = Review.objects.filter(product_id=product_id)
        ordering = request.query_params.get('ordering')
        reviews = reviews_services.ReviewService.apply_ordering(reviews, ordering)
        serializer = self.serializer_class(reviews, many=True)
        return Response(serializer.data)


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewCreateSerializer

    def post(self, request):
        """Создание нового отзыва."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            review = reviews_services.ReviewService.create_review(serializer.validated_data, request.user)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def patch(self, request, pk):
        """Обновление отзыва."""
        review = get_object_or_404(Review, pk=pk)
        serializer = self.serializer_class(review, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_review = reviews_services.ReviewService.update_review(review, serializer.validated_data,
                                                                              request.user)
                return Response(ReviewSerializer(updated_review).data, status=status.HTTP_200_OK)
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, review_id: int):
        """Получение списка комментариев для отзыва."""
        comments = Comment.objects.filter(review_id=review_id, parent=None)  # Только корневые
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        """Создание нового комментария."""
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            comment = comment_services.CommentService.create_comment(serializer.validated_data, request.user)
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentUpdateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def patch(self, request, pk: int):
        """Обновление комментария."""
        comment = get_object_or_404(Comment, pk=pk)
        serializer = CommentCreateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                updated_review = comment_services.CommentService.update_comment(comment, serializer.validated_data,
                                                                                request.user)
                return Response(CommentSerializer(updated_review).data, status=status.HTTP_200_OK)
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        review = get_object_or_404(Review, pk=pk)
        result = like_services.LikeService.toggle_review_like(review, request.user)
        return Response(result, status=status.HTTP_200_OK)


class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        comment = get_object_or_404(Comment, pk=pk)
        result = like_services.LikeService.toggle_comment_like(comment, request.user)
        return Response(result, status=status.HTTP_200_OK)
