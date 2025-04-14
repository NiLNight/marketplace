from django.urls import path
from apps.reviews.views import (
    ReviewListView,
    ReviewCreateView,
    ReviewUpdateView,
    CommentListView,
    CommentCreateView,
    CommentUpdateView,
    ReviewLikeView,
    CommentLikeView
)

urlpatterns = [
    path('<int:product_id>/', ReviewListView.as_view(), name='review-list'),
    path('create/', ReviewCreateView.as_view(), name='review-create'),
    path('update/<int:pk>/', ReviewUpdateView.as_view(), name='review-update'),
    path('comments/<int:review_id>/', CommentListView.as_view(), name='comment-list'),
    path('comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('comments/update/<int:pk>/', CommentUpdateView.as_view(), name='comment-update'),
    path('<int:pk>/like/', ReviewLikeView.as_view(), name='review-like'),
    path('comments/<int:pk>/like/', CommentLikeView.as_view(), name='comment-like'),
]
