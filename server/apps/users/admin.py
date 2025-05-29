from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from apps.users.models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Инлайн-класс для отображения профиля пользователя в админке.

    Позволяет редактировать данные профиля непосредственно на странице пользователя.

    Attributes:
        model: Модель профиля пользователя (UserProfile).
        can_delete (bool): Запрещает удаление профиля через админку.
        verbose_name (str): Название в единственном числе.
        verbose_name_plural (str): Название во множественном числе.
        fields (tuple): Поля для отображения и редактирования.
        readonly_fields (tuple): Поля, доступные только для чтения.
    """
    model = UserProfile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Данные профиля'
    fields = (
        'avatar',
        'phone',
        'birth_date',
        'public_id',
    )
    readonly_fields = ('public_id',)


class CustomUserAdmin(UserAdmin):
    """Кастомный администраторский класс для модели пользователя.

    Расширяет стандартный UserAdmin, добавляя инлайн для профиля и кастомные поля в списке.

    Attributes:
        inlines (tuple): Инлайн-классы для отображения связанных данных.
        list_display (tuple): Поля для отображения в списке пользователей.
    """
    inlines = (UserProfileInline,)
    list_display = (
        'username',
        'email',
        'date_joined',
        'get_phone',
        'get_avatar',
    )

    def get_phone(self, obj):
        """Возвращает номер телефона из профиля пользователя.

        Args:
            obj (User): Объект пользователя.

        Returns:
            str: Номер телефона или дефис, если профиль отсутствует.
        """
        return obj.profile.phone if hasattr(obj, 'profile') else '-'

    get_phone.short_description = 'Телефон'

    def get_avatar(self, obj):
        """Возвращает аватар из профиля пользователя.

        Args:
            obj (User): Объект пользователя.

        Returns:
            str: URL аватара или дефис, если профиль отсутствует.
        """
        return obj.profile.avatar if hasattr(obj, 'profile') else '-'

    get_avatar.short_description = 'Аватар'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Администраторский класс для модели профиля пользователя.

    Настраивает отображение, поиск и фильтрацию профилей в админке.

    Attributes:
        list_display (tuple): Поля для отображения в списке профилей.
        search_fields (tuple): Поля для поиска.
        list_filter (tuple): Поля для фильтрации.
        readonly_fields (tuple): Поля, доступные только для чтения.
    """
    list_display = (
        'user',
        'public_id',
        'phone',
        'birth_date',
        'avatar_tag',
    )
    search_fields = (
        'user__username',
        'public_id',
        'phone',
    )
    list_filter = ('birth_date',)
    readonly_fields = ('avatar_tag', 'public_id')

    def avatar_tag(self, obj):
        """Возвращает HTML-тег для предпросмотра аватара.

        Args:
            obj (UserProfile): Объект профиля пользователя.

        Returns:
            str: HTML-тег с изображением или дефис, если аватар отсутствует.
        """
        from django.utils.html import format_html
        return format_html(
            '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
            obj.avatar.url
        ) if obj.avatar else '-'

    avatar_tag.short_description = 'Превью аватара'


# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)