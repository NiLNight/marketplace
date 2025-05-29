"""Модуль URL-шаблонов для приложения wishlists.

Определяет маршруты для операций со списком желаний, таких как просмотр содержимого, добавление товаров и удаление товаров.
"""

from django.urls import path
from apps.wishlists.views import (
    WishlistAddView,
    WishlistItemDeleteView,
    WishlistGetView
)

urlpatterns = [
    path('add/', WishlistAddView.as_view(), name='wishlist-add'),
    path('delete/<int:pk>/', WishlistItemDeleteView.as_view(), name='wishlist-item-delete'),
    path('', WishlistGetView.as_view(), name='wishlist-get')
]
