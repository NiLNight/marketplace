"""Модуль URL-шаблонов для приложения carts.

Определяет маршруты для операций с корзиной, таких как просмотр содержимого, добавление товаров, обновление количества и удаление товаров.
"""

from django.urls import path

from apps.carts.views import (
    CartsAddView,
    CartsGetView,
    CartsItemUpdateView,
    CartsItemDeleteView,
)

app_name = 'carts'
urlpatterns = [
    path('', CartsGetView.as_view(), name='carts'),
    path('add/', CartsAddView.as_view(), name='cart_add'),
    path('<int:pk>/', CartsItemUpdateView.as_view(), name='cart_item'),
    path('delete/<int:pk>/', CartsItemDeleteView.as_view(), name='cart_item'),
]
