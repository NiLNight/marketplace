from django.contrib import admin
from apps.orders.models import Order, OrderItem, Delivery


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # количество пустых форм для добавления новых элементов


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created')
    list_filter = ('status', 'created')
    search_fields = ('user__username', 'id')
    inlines = [OrderItemInline]
    ordering = ('-created',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('order', 'product')
    search_fields = ('order__id', 'product__title')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'is_primary')
    list_filter = ('user', 'is_primary')
    search_fields = ('user__username', 'address')
