from django.apps import AppConfig


class CommentsConfig(AppConfig):
    """Конфигурация приложения comments.

    Определяет основные настройки приложения для управления комментариями.
    Включает функциональность древовидной структуры комментариев (MPTT),
    лайков и модерации.

    Attributes:
        default_auto_field (str): Тип поля для автоматически создаваемых первичных ключей.
        name (str): Полное имя приложения.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comments'
