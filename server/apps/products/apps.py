from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """Конфигурация приложения products.

    Определяет основные настройки приложения для управления продуктами.
    Включает функциональность категорий (MPTT), поиска через Elasticsearch,
    управления ценами, скидками и запасами.

    При инициализации подключает сигналы для автоматического обновления
    данных в Elasticsearch при изменении продуктов.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'

    def ready(self):
        """Выполняется при инициализации приложения.

        Импортирует модуль сигналов для автоматического обновления
        данных продуктов в Elasticsearch при их создании или изменении.
        """
        import apps.products.signals
