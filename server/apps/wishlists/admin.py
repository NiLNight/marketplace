"""Модуль административного интерфейса для приложения wishlists.

Определяет настройки отображения и управления моделями приложения wishlists
в административном интерфейсе Django.
"""

from django.contrib import admin
from apps.wishlists.models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели WishlistItem.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке элементов.
        list_filter (tuple): Поля для фильтрации элементов.
        search_fields (tuple): Поля для поиска элементов.
        raw_id_fields (tuple): Поля для выбора связанных объектов через поиск.
        readonly_fields (tuple): Поля, доступные только для чтения.
        date_hierarchy (str): Поле для иерархической навигации по датам.
    """
    list_display = ('user', 'product', 'created')
    list_filter = ('created', 'product__category')
    search_fields = ('user__username', 'user__email', 'product__title')
    raw_id_fields = ('user', 'product')
    readonly_fields = ('created', 'updated')
    date_hierarchy = 'created'
