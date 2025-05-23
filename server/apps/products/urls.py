from django.urls import path
from apps.products.views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    CategoryListView,
)

app_name = 'products'

urlpatterns = [
    path('list/', ProductListView.as_view(), name='list'),
    path('create/', ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='delete'),
    path('categories/', CategoryListView.as_view(), name='category')
]
