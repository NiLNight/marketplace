from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """Конфигурация приложения orders.

    Определяет основные настройки приложения для управления заказами.
    Автоматически подключает сигналы при инициализации.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'

    def ready(self):
        """Выполняется при инициализации приложения.

        Импортирует модуль сигналов для их регистрации.
        """
        import apps.orders.signals