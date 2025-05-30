"""Модуль URL-шаблонов для приложения comments.

Определяет маршруты для операций с комментариями, таких как просмотр списка, создание, обновление, управление лайками и удаление.
"""

from django.urls import path
from apps.comments.views import (
    CommentListView,
    CommentCreateView,
    CommentUpdateView,
    CommentLikeView, CommentDeleteView
)

urlpatterns = [
    path('<int:review_id>/', CommentListView.as_view(), name='comment-list'),
    path('create/', CommentCreateView.as_view(), name='comment-create'),
    path('update/<int:pk>/', CommentUpdateView.as_view(), name='comment-update'),
    path('<int:pk>/like/', CommentLikeView.as_view(), name='comment-like'),
    path('delete/<int:pk>/', CommentDeleteView.as_view(), name='comment-delete'),
]
