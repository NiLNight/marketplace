from django.urls import path
from apps.reviews.views import (
    ReviewListView,
    ReviewCreateView,
    ReviewUpdateView,
    ReviewLikeView,
)

urlpatterns = [
    path('<int:product_id>/', ReviewListView.as_view(), name='review-list'),
    path('create/', ReviewCreateView.as_view(), name='review-create'),
    path('update/<int:pk>/', ReviewUpdateView.as_view(), name='review-update'),
    path('<int:pk>/like/', ReviewLikeView.as_view(), name='review-like'),
]
