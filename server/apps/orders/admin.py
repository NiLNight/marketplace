# orders/admin.py
from django.contrib import admin
from .models import Order, Delivery
from apps.carts.models import OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity')
    readonly_fields = ('product', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'delivery', 'created')
    list_filter = ('status', 'created')
    search_fields = ('id', 'user__email')
    inlines = [OrderItemInline]
    readonly_fields = ('created', 'updated')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'cost', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('address', 'user__email')
