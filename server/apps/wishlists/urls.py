"""Модуль URL-шаблонов для приложения wishlists.

Определяет маршруты для операций со списком желаний, таких как просмотр содержимого, добавление товаров и удаление товаров.
"""

from django.urls import path
from apps.wishlists.views import (
    WishlistAddView,
    WishlistItemDeleteView,
    WishlistGetView
)

app_name = 'wishlists'

urlpatterns = [
    path('add/', WishlistAddView.as_view(), name='wishlist_add'),
    path('delete/<int:pk>/', WishlistItemDeleteView.as_view(), name='wishlist_item_delete'),
    path('', WishlistGetView.as_view(), name='wishlist_get')
]
