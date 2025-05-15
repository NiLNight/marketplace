from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.core.services.cache_services import CacheService
from apps.delivery.models import Delivery, PickupPoint, City
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Delivery)
def invalidate_delivery_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка адресов доставки при сохранении или удалении объекта Delivery.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели Delivery.
        kwargs: Дополнительные аргументы сигнала.
    """
    cache_key = f"delivery_list:{instance.user.id}"
    CacheService.invalidate_cache(prefix=cache_key)
    logger.info(f"Invalidated cache for delivery_list user_id={instance.user.id}")


@receiver([post_save, post_delete], sender=PickupPoint)
def invalidate_pickup_point_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка пунктов выдачи при сохранении или удалении объекта PickupPoint.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели PickupPoint.
        kwargs: Дополнительные аргументы сигнала.
    """
    cache_key = f"pickup_points:{instance.city_id or 'all'}:none"
    CacheService.invalidate_cache(prefix=cache_key)
    logger.info(f"Invalidated cache for pickup_points city_id={instance.city_id}")


@receiver([post_save, post_delete], sender=City)
def invalidate_city_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка городов при сохранении или удалении объекта City.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели City.
        kwargs: Дополнительные аргументы сигнала.
    """
    cache_key = "city_list"
    CacheService.invalidate_cache(prefix=cache_key)
    logger.info(f"Invalidated cache for city_list")
