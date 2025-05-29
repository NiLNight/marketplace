"""Модуль административного интерфейса для приложения reviews.

Определяет настройки отображения и управления моделью Review
в административном интерфейсе Django.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Review.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке отзывов.
        list_filter (tuple): Поля для фильтрации отзывов.
        search_fields (tuple): Поля для поиска отзывов.
        raw_id_fields (tuple): Поля для выбора связанных объектов через поиск.
        readonly_fields (tuple): Поля, доступные только для чтения.
        date_hierarchy (str): Поле для иерархической навигации по датам.
    """
    list_display = ('id', 'user', 'product', 'value', 'created')
    list_filter = ('value', 'created')
    search_fields = ('user__username', 'user__email', 'text', 'product__title')
    raw_id_fields = ('user', 'product')
    readonly_fields = ('created', 'updated')
    date_hierarchy = 'created'
