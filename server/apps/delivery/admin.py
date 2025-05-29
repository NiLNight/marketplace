"""Модуль административного интерфейса для приложения delivery.

Определяет настройки отображения и управления моделями City и PickupPoint
в административном интерфейсе Django.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.delivery.models import City, PickupPoint


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели City.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке городов.
        search_fields (tuple): Поля для поиска городов.
        ordering (tuple): Поля для сортировки городов.
    """
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели PickupPoint.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке пунктов выдачи.
        list_filter (tuple): Поля для фильтрации пунктов выдачи.
        search_fields (tuple): Поля для поиска пунктов выдачи.
        raw_id_fields (tuple): Поля для выбора связанных объектов через поиск.
        readonly_fields (tuple): Поля, доступные только для чтения.
    """
    list_display = ('city', 'address', 'district', 'is_active')
    list_filter = ('city', 'district', 'is_active')
    search_fields = ('address', 'district', 'city__name')
    raw_id_fields = ('city',)
    readonly_fields = ('search_vector',)
