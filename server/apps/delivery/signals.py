from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import redis
from apps.core.services.cache_services import CacheService
from apps.delivery.models import PickupPoint, City
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=PickupPoint)
def invalidate_pickup_point_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка пунктов выдачи при сохранении или удалении объекта PickupPoint.
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
    """
    try:
        cache_key = "city_list"
        CacheService.invalidate_cache(prefix=cache_key)
        logger.info(f"Invalidated cache for city_list")
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error invalidating city_list: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error invalidating city_list: {str(e)}")
