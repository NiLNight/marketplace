import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from apps.orders.models import Order
from apps.orders.services.notification_services import NotificationService
from apps.products.services.tasks import update_popularity_score
from apps.core.services.cache_services import CacheService
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def track_status(sender, instance, **kwargs):
    """
    Отслеживает исходный статус заказа перед сохранением.

    Сохраняет текущий статус заказа в атрибут `__original_status` для последующего сравнения
    в сигнале post_save. Для новых заказов устанавливает `__original_status` как None.

    Args:
        sender: Класс модели, отправивший сигнал (Order).
        instance: Экземпляр модели Order, который сохраняется.
        kwargs: Дополнительные аргументы сигнала.

    Returns:
        None: Метод только устанавливает атрибут и не возвращает значения.

    Raises:
        ObjectDoesNotExist: Если заказ не найден в базе данных во время pre_save.
    """
    logger.debug(f"Tracking status for order={instance.id or 'new'}, user={instance.user.id}")
    try:
        if instance.pk:
            instance.__original_status = Order.objects.get(pk=instance.pk).status
        else:
            instance.__original_status = None
    except ObjectDoesNotExist:
        logger.warning(f"Order {instance.pk} not found during pre_save for user={instance.user.id}")
        instance.__original_status = None


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Обрабатывает событие сохранения заказа и отправляет уведомления.

    При создании заказа или изменении его статуса отправляет соответствующее уведомление
    пользователю через NotificationService и инвалидирует кэш.

    Args:
        sender: Класс модели, отправивший сигнал (Order).
        instance: Экземпляр модели Order, который был сохранен.
        created (bool): Флаг, указывающий, был ли заказ создан.
        kwargs: Дополнительные аргументы сигнала.

    Returns:
        None: Метод только отправляет уведомления и инвалидирует кэш.

    Raises:
        Exception: Если обработка события сохранения не удалась из-за проблем с уведомлениями или кэшем.
    """
    logger.debug(f"Starting post_save for order={instance.id}, user={instance.user.id}")
    try:
        delivery_info = f"{_('Пункт выдачи')}: {instance.pickup_point.city.name}, {instance.pickup_point.address}"
        if created:
            NotificationService.send_notification(
                instance.user, f"{_('Ваш заказ')} #{instance.id} {_('создан')}. {delivery_info}"
            )
            logger.info(f"Notification queued for order creation, "
                        f"order={instance.id}, user={instance.user.id}")
        elif hasattr(instance, "__original_status") and instance.status != instance.__original_status:
            if instance.status == 'delivered':
                NotificationService.send_notification(
                    instance.user, f"{_('Ваш заказ')} #{instance.id} {_('доставлен')}! {delivery_info}"
                )
                logger.info(f"Notification queued for order delivered, "
                            f"order={instance.id}, user={instance.user.id}")
                order_items = instance.order_items.select_related('product')
                for item in order_items:
                    update_popularity_score.delay(item.product.id)
                    logger.info(f"Scheduled popularity score update for product={item.product.id}"
                                f" in order={instance.id}")
            else:
                NotificationService.send_notification(
                    instance.user,
                    f"{_('Статус заказа')} #{instance.id} {_('изменен на')} {instance.status}. {delivery_info}"
                )
                logger.info(f"Notification queued for status change, "
                            f"order={instance.id}, user={instance.user.id}")

        # Инвалидация кэша после изменения заказа
        CacheService.invalidate_cache(prefix=f"order_list:{instance.user.id}")
        CacheService.invalidate_cache(prefix=f"order_detail:{instance.id}:{instance.user.id}")
        logger.info(f"Invalidated cache for order={instance.id}, user={instance.user.id}")
    except Exception as e:
        logger.error(f"Failed to process post_save for order={instance.id},"
                     f" user={instance.user.id}: {str(e)}")
