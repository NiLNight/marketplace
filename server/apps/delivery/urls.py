"""
Модуль URL-шаблонов для приложения delivery.

Определяет маршруты для операций с пунктами выдачи и списком городов.
"""
from django.urls import path

from apps.delivery.views import (
    CityListView,
    PickupPointListView,
)

app_name = 'delivery'

urlpatterns = [
    path('pickup_points/', PickupPointListView.as_view(), name='pickup_points'),
    path('city_list/', CityListView.as_view(), name='city_list'),
]