"""Модуль администрирования для приложения comments.

Регистрирует модель Comment в административном интерфейсе Django.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from mptt.admin import MPTTModelAdmin
from apps.comments.models import Comment


@admin.register(Comment)
class CommentAdmin(MPTTModelAdmin):
    """Административный интерфейс для модели Comment.

    Attributes:
        list_display (tuple): Поля, отображаемые в списке комментариев.
        list_filter (tuple): Поля для фильтрации комментариев.
        search_fields (tuple): Поля для поиска комментариев.
        raw_id_fields (tuple): Поля для выбора связанных объектов через поиск.
        readonly_fields (tuple): Поля, доступные только для чтения.
        mptt_level_indent (int): Отступ для уровней иерархии (20 пикселей).
        date_hierarchy (str): Поле для иерархической навигации по датам.
    """
    list_display = ('id', 'user', 'review', 'text_preview', 'created')
    list_filter = ('created', 'review__product')
    search_fields = ('text', 'user__username', 'review__product__title')
    raw_id_fields = ('user', 'review', 'parent')
    readonly_fields = ('created', 'updated')
    mptt_level_indent = 20
    date_hierarchy = 'created'

    def text_preview(self, obj):
        """Возвращает сокращенный текст комментария.

        Args:
            obj: Объект Comment.

        Returns:
            str: Первые 50 символов текста комментария.
        """
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = _('Текст комментария')
