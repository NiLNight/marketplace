"""Модуль административного интерфейса для приложения orders.

Определяет настройки отображения и управления моделью Order
в административном интерфейсе Django.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Order.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке заказов.
        list_filter (tuple): Поля для фильтрации заказов.
        search_fields (tuple): Поля для поиска заказов.
        raw_id_fields (tuple): Поля для выбора связанных объектов через поиск.
        readonly_fields (tuple): Поля, доступные только для чтения.
        date_hierarchy (str): Поле для иерархической навигации по датам.
    """
    list_display = ('id', 'user', 'status', 'total_price', 'pickup_point', 'created')
    list_filter = ('status', 'created')
    search_fields = ('user__username', 'user__email', 'pickup_point__address')
    raw_id_fields = ('user', 'pickup_point')
    readonly_fields = ('created', 'updated')
    date_hierarchy = 'created'