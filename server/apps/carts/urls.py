from django.urls import path

from apps.carts.views import (
    CartsAddView
)

app_name = 'carts'
urlpatterns = [
    path('add/', CartsAddView.as_view(), name='cart_add'),
    path('<int:pk>/', CartsView.as_view(), name='cart_item'),
]
