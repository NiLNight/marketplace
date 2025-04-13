from django.urls import path
from apps.reviews.views import (
    ReviewListView,
    ReviewCreateView,
    ReviewUpdateView,
    CommentListView,
    CommentCreateView,
    CommentUpdateView,
)

urlpatterns = [
    path('<int:pk>/', ReviewListView.as_view(), name='review-list'),
    path('add/', ReviewCreateView.as_view(), name='review-create'),
    path('update/<int:pk>/', ReviewUpdateView.as_view(), name='review-update'),
    path('comment/<int:pk>/', CommentListView.as_view(), name='comment-list'),
    path('comment/create/', CommentCreateView.as_view(), name='comment-create'),
    path('comment/update/<int:pk>/', CommentUpdateView.as_view(), name='comment-update'),
]