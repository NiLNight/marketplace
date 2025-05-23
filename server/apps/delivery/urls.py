from django.urls import path

from apps.delivery.views import (
    CityListView,
    PickupPointListView,
)

urlpatterns = [
    path('pickup_points/', PickupPointListView.as_view(), name='pickup_points'),
    path('city_list/', CityListView.as_view(), name='city_list'),
]