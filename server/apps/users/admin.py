from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from apps.users.models import UserProfile


class UserProfileInline(admin.StackedInline):
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
    inlines = (UserProfileInline,)
    list_display = (
        'username',
        'email',
        'date_joined',
        'get_phone',
        'get_avatar',
    )

    def get_phone(self, obj):
        return obj.profile.phone if hasattr(obj, 'profile') else '-'

    get_phone.short_description = 'Телефон'

    def get_avatar(self, obj):
        return obj.profile.avatar if hasattr(obj, 'profile') else '-'

    get_avatar.short_description = 'Аватар'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
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
        from django.utils.html import format_html
        return format_html(
            '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
            obj.avatar.url
        ) if obj.avatar else '-'

    avatar_tag.short_description = 'Превью аватара'


# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)