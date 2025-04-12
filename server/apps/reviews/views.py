from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reviews.models import Review
from apps.reviews.services import reviews_services

from apps.reviews.serializers import (
    ReviewCreateSerializer,
    ReviewSerializer
)


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewCreateSerializer

    def post(self, request):
        """Создание нового отзыва."""
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        if serializer.is_valid():
            review = reviews_services.ReviewService.create_review(serializer.validated_data, request.user)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewUpdateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewCreateSerializer

    def patch(self, request, pk):
        """Обновление отзыва."""
        review = get_object_or_404(Review, pk=pk)
        serializer = self.serializer_class(review, data=request.data, partial=True)
        if serializer.is_valid():
            updated_review = reviews_services.ReviewService.update_review(review, serializer.validated_data)
            return Response(ReviewSerializer(updated_review).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
