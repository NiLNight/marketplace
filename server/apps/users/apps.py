from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения users.

    Определяет основные настройки приложения для управления пользователями.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
