import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

from apps.orders.models import Order
from apps.orders.services.notification_services import NotificationService
from apps.products.services.tasks import update_popularity_score

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def track_status(sender, instance, **kwargs):
    """Отслеживает исходный статус заказа перед сохранением.

    Сохраняет текущий статус заказа в атрибут `__original_status` для последующего сравнения
    в сигнале post_save. Для новых заказов устанавливает `__original_status` как None.

    Args:
        sender: Класс модели, отправивший сигнал (Order).
        instance: Экземпляр модели Order, который сохраняется.
        **kwargs: Дополнительные аргументы сигнала.
    """
    logger.debug(f"Tracking status for order={instance.id or 'new'}, user={instance.user.id}")
    try:
        if instance.pk:  # Если объект уже существует
            instance.__original_status = Order.objects.get(pk=instance.pk).status
        else:  # Новый объект
            instance.__original_status = None
    except ObjectDoesNotExist:
        logger.warning(f"Order {instance.pk} not found during pre_save for user={instance.user.id}")
        instance.__original_status = None


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """Обрабатывает событие сохранения заказа и отправляет уведомления.

    При создании заказа или изменении его статуса отправляет соответствующее уведомление
    пользователю через NotificationService.

    Args:
        sender: Класс модели, отправивший сигнал (Order).
        instance: Экземпляр модели Order, который был сохранен.
        created (bool): Флаг, указывающий, был ли заказ создан.
        **kwargs: Дополнительные аргументы сигнала.
    """
    logger.info(f"Processing post_save for order={instance.id}, user={instance.user.id}, created={created}")
    try:
        if created:
            NotificationService.send_notification(
                instance.user, f"Ваш заказ #{instance.id} создан"
            )
            logger.info(f"Notification queued for order creation, order={instance.id}, user={instance.user.id}")
        elif hasattr(instance, "__original_status") and instance.status != instance.__original_status:
            if instance.status == 'delivered':
                NotificationService.send_notification(
                    instance.user, f"Ваш заказ #{instance.id} доставлен!"
                )
                logger.info(f"Notification queued for order delivered, order={instance.id}, user={instance.user.id}")
                # Обновляем popularity_score для всех продуктов в заказе
                order_items = instance.order_items.select_related('product')
                for item in order_items:
                    update_popularity_score.delay(item.product.id)
                    logger.info(
                        f"Scheduled popularity score update for product={item.product.id} in order={instance.id}")
            else:
                NotificationService.send_notification(
                    instance.user, f"Статус заказа #{instance.id} изменен на {instance.status}"
                )
                logger.info(f"Notification queued for status change, order={instance.id}, user={instance.user.id}")
    except Exception as e:
        logger.error(f"Failed to process post_save for order={instance.id}, user={instance.user.id}: {str(e)}")
