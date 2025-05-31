"""Модуль URL-шаблонов для приложения products.

Определяет маршруты для операций с продуктами и просмотра категорий.
"""

from django.urls import path
from apps.products.views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    CategoryListView,
    CategoryDetailView,
)

app_name = 'products'

urlpatterns = [
    path('list/', ProductListView.as_view(), name='product_list'),
    path('create/', ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
]
