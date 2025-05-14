# orders/admin.py
from django.contrib import admin
from .models import Order, Delivery
from apps.carts.models import OrderItem


admin.site.register(Order)