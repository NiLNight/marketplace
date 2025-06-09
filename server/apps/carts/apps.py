from django.apps import AppConfig


class CartsConfig(AppConfig):
    """Конфигурация приложения carts.

    Определяет основные настройки приложения для управления корзинами пользователей.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.carts'

    def ready(self):
        import apps.carts.signals
