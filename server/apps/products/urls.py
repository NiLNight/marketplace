from django.urls import path
from apps.products.views import ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView

app_name = 'products'

urlpatterns = [
    path('list/', ProductListView.as_view(), name='list'),
    path('create/', ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', ProductUpdateView.as_view(), name='update'),
]