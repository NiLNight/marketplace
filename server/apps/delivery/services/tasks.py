from celery import shared_task

from apps.delivery.documents import PickupPointDocument
from apps.delivery.models import PickupPoint
import logging

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(ConnectionError,), max_retries=3, countdown=60)
def index_pickup_point(pickup_point_id):
    """
    Асинхронно индексирует пункт выдачи в Elasticsearch.

    Args:
        pickup_point_id (int): Идентификатор пункта выдачи.
    """
    try:
        pickup_point = PickupPoint.objects.get(pk=pickup_point_id)
        doc = PickupPointDocument(
            meta={'id': pickup_point.id},
            address=pickup_point.address,
            is_active=pickup_point.is_active,
            city_id=pickup_point.city.id
        )
        doc.instance = pickup_point
        doc.save()
        logger.info(f"Indexed pickup_point id={pickup_point_id}, "
                    f"task_id={index_pickup_point.request.id}")
    except PickupPoint.DoesNotExist:
        logger.warning(f"PickupPoint id={pickup_point_id} not found for indexing, "
                       f"task_id={index_pickup_point.request.id}")
    except Exception as e:
        logger.error(f"Failed to index pickup_point id={pickup_point_id}: {str(e)}, "
                     f"task_id={index_pickup_point.request.id}")
