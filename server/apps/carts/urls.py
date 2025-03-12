from django.urls import path

from apps.carts.views import (
    CartsView
)

app_name = 'carts'
urlpatterns = [
    path('', CartsView.as_view(), name='cart'),
    path('<int:pk>/', CartsView.as_view(), name='cart_item'),
]
