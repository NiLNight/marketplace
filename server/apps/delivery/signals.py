from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import redis
from apps.core.services.cache_services import CacheService
from apps.delivery.models import PickupPoint, City
from apps.delivery.services.tasks import update_search_vector
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=PickupPoint)
def invalidate_pickup_point_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш пунктов выдачи при сохранении или удалении объекта.

    Args:
        sender (Model): Класс модели.
        instance (PickupPoint): Экземпляр модели.
        kwargs (dict): Дополнительные аргументы.

    Returns:
        None: Метод только инвалидирует кэш.

    Raises:
        redis.exceptions.RedisError: Если Redis недоступен.
        Exception: Если произошла непредвиденная ошибка при инвалидации кэша.
    """
    try:
        city_id = instance.city_id or 'all'
        CacheService.invalidate_cache(prefix=f"pickup_points:{city_id}")
        logger.info(
            f"Invalidated cache for pickup_points CityID={city_id}, "
            f"task_id={getattr(instance, 'task_id', 'unknown')}"
        )
    except redis.exceptions.RedisError as e:
        logger.error(
            f"Redis error invalidating cache for pickup_points CityID={city_id}: {str(e)}, "
            f"task_id={getattr(instance, 'task_id', 'unknown')}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error invalidating cache for pickup_points CityID={city_id}: {str(e)}, "
            f"task_id={getattr(instance, 'task_id', 'unknown')}"
        )


@receiver([post_save, post_delete], sender=City)
def invalidate_city_cache(sender, instance, **kwargs):
    """
    Инвалидирует кэш списка городов и районов, обновляет поисковые векторы.

    Args:
        sender (Model): Класс модели.
        instance (City): Экземпляр модели.
        kwargs (dict): Дополнительные аргументы.

    Returns:
        None: Метод только инвалидирует кэш и запускает обновление поисковых векторов.

    Raises:
        redis.exceptions.RedisError: Если Redis недоступен.
        Exception: Если произошла непредвиденная ошибка при инвалидации кэша или обновлении векторов.
    """
    try:
        CacheService.invalidate_cache(prefix="city_list")
        CacheService.invalidate_cache(prefix=f"districts:{instance.id}")
        logger.info(
            f"Invalidated cache for city_list and districts CityID={instance.id}, "
            f"task_id={getattr(instance, 'task_id', 'unknown')}"
        )
        # Асинхронное обновление search_vector для связанных пунктов выдачи
        for pickup_point in instance.pickup_points.all():
            task = update_search_vector.delay(pickup_point.id)
            logger.info(
                f"Triggered search_vector update for pickup_point ID={pickup_point.id}, "
                f"task_id={task.id}, CityID={instance.id}"
            )
    except redis.exceptions.RedisError as e:
        logger.error(
            f"Redis error invalidating cache for city_list and districts: {str(e)}, "
            f"task_id={getattr(instance, 'task_id', 'unknown')}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error invalidating cache for city_list and districts: {str(e)}, "
            f"task_id={getattr(instance, 'task_id', 'unknown')}"
        )
