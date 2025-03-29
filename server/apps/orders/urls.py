from django.urls import path

from apps.orders.views import (
    OrderCreateView,
    OrderListView,
    OrderDetailView
)

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('create/', OrderCreateView.as_view(), name='order_create')
]