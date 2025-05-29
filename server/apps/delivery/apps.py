from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    """Конфигурация приложения delivery.

    Определяет основные настройки приложения для управления доставкой и пунктами выдачи.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.delivery'
