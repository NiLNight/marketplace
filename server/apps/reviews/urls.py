from django.urls import path
from apps.reviews.views import (
    ReviewCreateView,
    ReviewUpdateView
)

urlpatterns = [
    path('add/', ReviewCreateView.as_view(), name='review-create'),
    path('update/<int:pk>/', ReviewUpdateView.as_view(), name='review-update'),
]