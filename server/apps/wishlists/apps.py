from django.apps import AppConfig


class WishlistsConfig(AppConfig):
    """Конфигурация приложения wishlists.

    Определяет основные настройки приложения для управления списками желаний пользователей.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
        verbose_name (str): Отображаемое имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wishlists'
    verbose_name = 'Списки желаний'
