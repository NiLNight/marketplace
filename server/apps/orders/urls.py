from django.urls import path

from apps.orders.views import (
    OrderCreateView,
    OrderListView
)

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('create/', OrderCreateView.as_view(), name='order_create')
]