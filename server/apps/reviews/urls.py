from django.urls import path
from apps.reviews.views import (
    ReviewListView,
    ReviewCreateView,
    ReviewUpdateView
)

urlpatterns = [
    path('<int:pk>/', ReviewListView.as_view(), name='review-list'),
    path('add/', ReviewCreateView.as_view(), name='review-create'),
    path('update/<int:pk>/', ReviewUpdateView.as_view(), name='review-update'),
]