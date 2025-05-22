from django.urls import path

from apps.delivery.views import (
    CityListView,
    PickupPointListView,
    DistrictListView,
)

urlpatterns = [
    path('pickup_points/', PickupPointListView.as_view(), name='pickup_points'),
    path('city_list/', CityListView.as_view(), name='city_list'),
    path('district_list/', DistrictListView.as_view(), name='district_list'),
]