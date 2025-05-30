"""Модуль сигналов для приложения products.

Содержит обработчики сигналов для автоматического обновления данных
при создании, изменении или удалении продуктов.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.products.models import Product
from apps.products.services.tasks import update_elasticsearch_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def update_product_in_elasticsearch(sender, instance, created, **kwargs):
    """Запускает асинхронную задачу для обновления данных продукта в Elasticsearch.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели Product, который был сохранен.
        created (bool): Флаг, указывающий, был ли объект создан (True) или обновлен (False).
        **kwargs: Дополнительные аргументы, переданные сигналом.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        None: Функция не вызывает исключений напрямую, но может логировать ошибки.
    """
    user_id = instance.user.id if instance.user else 'anonymous'
    action = 'Creating' if created else 'Updating'
    # Пропускаем сигнал, если обновляется только popularity_score
    if kwargs.get('update_fields') == {'popularity_score'}:
        logger.debug(f"Skipping signal for product {instance.id} due to popularity_score update")
        return
    logger.info(f"{action} product: title={instance.title}, user={user_id}, is_active={instance.is_active}")
    update_elasticsearch_task.delay(instance.id)


@receiver(post_delete, sender=Product)
def delete_product_from_elasticsearch(sender, instance, **kwargs):
    """Запускает асинхронную задачу для удаления данных продукта из Elasticsearch.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели Product, который был удален.
        **kwargs: Дополнительные аргументы, переданные сигналом.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        None: Функция не вызывает исключений напрямую, но может логировать ошибки.
    """
    user_id = instance.user.id if instance.user else 'anonymous'
    logger.info(f"Deleting product from Elasticsearch: title={instance.title}, user={user_id}")
    update_elasticsearch_task.delay(instance.id, delete=True)
