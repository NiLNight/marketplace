from django.urls import path
from apps.wishlists.views import (
    WishlistAddView,
)

urlpatterns = [
    path('add/', WishlistAddView.as_view(), name='wishlist-add')
]
