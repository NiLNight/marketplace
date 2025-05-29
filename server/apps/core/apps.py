from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Конфигурация приложения core.

    Определяет основные настройки базового приложения, предоставляющего общие модели,
    утилиты и сервисы для других приложений проекта.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
