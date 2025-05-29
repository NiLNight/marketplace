"""Модуль административного интерфейса для приложения core.

Определяет настройки отображения и управления моделями приложения core
в административном интерфейсе Django.
"""

from django.contrib import admin
from apps.core.models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Административный интерфейс для модели Like.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке лайков.
        list_filter (tuple): Поля для фильтрации лайков.
        search_fields (tuple): Поля для поиска лайков.
        raw_id_fields (tuple): Поля для выбора связанных объектов через поиск.
        readonly_fields (tuple): Поля, доступные только для чтения.
        date_hierarchy (str): Поле для иерархической навигации по датам.
    """
    list_display = ('user', 'content_type', 'object_id', 'created')
    list_filter = ('content_type', 'created')
    search_fields = ('user__username', 'user__email', 'object_id')
    raw_id_fields = ('user',)
    readonly_fields = ('created', 'updated')
    date_hierarchy = 'created'
