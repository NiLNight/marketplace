import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.products.services.tasks import update_popularity_score

from apps.carts.models import OrderItem

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrderItem)
def order_item_post_save(sender, instance, created, **kwargs):
    """
    Обрабатывает событие сохранения OrderItem и обновляет популярность продукта.

    Args:
        sender: Класс модели, отправивший сигнал (OrderItem).
        instance: Экземпляр модели OrderItem.
        created: Флаг, указывающий, был ли объект создан.
        kwargs: Дополнительные аргументы сигнала.

    Returns:
        None: Вызывает задачу обновления популярности продукта.
    """
    logger.debug(f"Starting post_save for order_item={instance.id}, product={instance.product.id}")
    try:
        # Вызываем обновление популярности только если OrderItem привязан к заказу
        if instance.order and instance.order.status == 'processing':
            update_popularity_score.delay(instance.product.id)
            logger.info(f"Scheduled popularity score update for product={instance.product.id}"
                        f" in order={instance.order.id}")
    except Exception as e:
        logger.error(f"Failed to process post_save for order_item={instance.id}: {str(e)}")
