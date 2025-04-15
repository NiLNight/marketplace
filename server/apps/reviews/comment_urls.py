from django.urls import path
from apps.reviews.views import (
    CommentListView,
    CommentCreateView,
    CommentUpdateView,
    CommentLikeView
)

urlpatterns = [
    path('<int:review_id>/', CommentListView.as_view(), name='comment-list'),
    path('create/', CommentCreateView.as_view(), name='comment-create'),
    path('update/<int:pk>/', CommentUpdateView.as_view(), name='comment-update'),
    path('<int:pk>/like/', CommentLikeView.as_view(), name='comment-like'),
]
