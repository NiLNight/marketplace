"""Модуль сигналов для приложения reviews.

Содержит обработчики сигналов для автоматического обновления данных
при создании, изменении или удалении отзывов.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.core.services.cache_services import CacheService
from apps.reviews.models import Review
from apps.products.services.tasks import update_elasticsearch_task, update_popularity_score

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Review)
def update_product_data(sender, instance, **kwargs):
    """Обновляет данные продукта после изменения отзыва.

    Запускает асинхронные задачи для обновления:
    - Данных продукта в Elasticsearch
    - Показателя популярности продукта
    - Инвалидирует все связанные кэши

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр Review, который был изменен.
        **kwargs: Дополнительные аргументы сигнала.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        None: Функция не вызывает исключений напрямую, но может логировать ошибки.
    """
    user_id = instance.user.id if instance.user else 'anonymous'
    product_id = instance.product.id
    action = 'deleted' if kwargs.get('signal') == post_delete else 'saved'
    logger.info(f"Review {instance.id} {action} for product={product_id}, user={user_id}")

    CacheService.invalidate_cache(prefix=f"reviews:{instance.product_id}")

    # Обновляем данные в Elasticsearch и показатель популярности
    update_elasticsearch_task.delay(product_id)
    update_popularity_score.delay(product_id)
