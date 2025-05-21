from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import redis
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
    try:
        if not instance.user:
            logger.warning(f"Delivery instance {instance.id} has no associated user")
            return
        cache_key = f"delivery_list:{instance.user.id}"
        CacheService.invalidate_cache(prefix=cache_key)
        logger.info(f"Invalidated cache for delivery_list user_id={instance.user.id}")
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error invalidating delivery_list user_id={instance.user.id}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error invalidating delivery_list user_id={instance.user.id}: {str(e)}")


@receiver([post_save, post_delete], sender=PickupPoint)
def invalidate_pickup_point_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка пунктов выдачи при сохранении или удалении объекта PickupPoint.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели PickupPoint.
        kwargs: Дополнительные аргументы сигнала.
    """
    try:
        cache_key = f"pickup_points:{instance.city_id or 'all'}:none"
        CacheService.invalidate_cache(prefix=cache_key)
        logger.info(f"Invalidated cache for pickup_points city_id={instance.city_id}")
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error invalidating pickup_points city_id={instance.city_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error invalidating pickup_points city_id={instance.city_id}: {str(e)}")


@receiver([post_save, post_delete], sender=City)
def invalidate_city_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка городов при сохранении или удалении объекта City.

    Args:
        sender: Класс модели, отправивший сигнал.
        instance: Экземпляр модели City.
        kwargs: Дополнительные аргументы сигнала.
    """
    try:
        cache_key = "city_list"
        CacheService.invalidate_cache(prefix=cache_key)
        logger.info(f"Invalidated cache for city_list")
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error invalidating city_list: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error invalidating city_list: {str(e)}")
