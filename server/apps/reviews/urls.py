from django.urls import path
from apps.reviews.views import (
    ReviewCreateView
)

urlpatterns = [
    path('add/', ReviewCreateView.as_view(), name='review-create'),
]