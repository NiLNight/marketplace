from django.urls import path
from apps.products.views import ProductListView, ProductDetailView

app_name = 'products'

urlpatterns = [
    path('list/', ProductListView.as_view(), name='list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
]