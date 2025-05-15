from django.urls import path

from apps.delivery.views import (
    CityListView,
    PickupPointListView,
    DeliveryListView
)

urlpatterns = [
    path('pickup_points/', PickupPointListView.as_view(), name='pickup_points'),
    path('deliveries/', DeliveryListView.as_view(), name='deliveries'),
    path('city_list/', CityListView.as_view(), name='city_list'),
]