from django.urls import path
from apps.wishlists.views import (
    WishlistAddView,
    WishlistItemDeleteView,
    WishlistGetView
)

urlpatterns = [
    path('add/', WishlistAddView.as_view(), name='wishlist-add'),
    path('delete/<int:pk>/', WishlistItemDeleteView.as_view(), name='wishlist-item-delete'),
    path('', WishlistGetView.as_view(), name='wishlist-get')
]
