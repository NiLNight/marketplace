from django.urls import path
from apps.products.views import ProductListView

app_name = 'products'

urlpatterns = [
    path('list/', ProductListView.as_view(), name='list'),
]