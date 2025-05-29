from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """Конфигурация приложения reviews.

    Определяет основные настройки приложения для управления отзывами и комментариями.
    Включает функциональность оценок, комментирования и модерации контента.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews'

    def ready(self):
        """Выполняется при инициализации приложения.

        Импортирует модуль сигналов для их регистрации.
        """
        import apps.reviews.signals
