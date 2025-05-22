from celery import shared_task
from apps.delivery.documents import PickupPointDocument
from apps.delivery.exceptions import PickupPointNotFound
from apps.delivery.models import PickupPoint
from elasticsearch_dsl.exceptions import ElasticsearchDslException
import logging

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(ConnectionError,), max_retries=3, retry_backoff=60)
def index_pickup_point(pickup_point_id):
    """
    Асинхронно индексирует пункт выдачи в Elasticsearch.
    """
    try:
        pickup_point = PickupPoint.objects.get(pk=pickup_point_id)
        if not pickup_point.city:
            logger.warning(f"Pickup point id={pickup_point_id} has no associated city")
            return
        doc = PickupPointDocument(
            meta={'id': pickup_point.id},
            address=pickup_point.address,
            district=pickup_point.district or '',
            is_active=pickup_point.is_active,
            city={'id': pickup_point.city.id, 'name': pickup_point.city.name}
        )
        doc.instance = pickup_point
        doc.save()
        logger.info(f"Indexed pickup_point id={pickup_point_id},"
                    f" task_id={index_pickup_point.request.id}")
    except PickupPoint.DoesNotExist:
        logger.error(f"PickupPoint id={pickup_point_id} not found for indexing")
        raise PickupPointNotFound(f"Пункт выдачи с ID {pickup_point_id} не найден")
    except ElasticsearchDslException as e:
        logger.error(f"Elasticsearch error indexing pickup_point id={pickup_point_id}: {str(e)},"
                     f" task_id={index_pickup_point.request.id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error indexing pickup_point id={pickup_point_id}: {str(e)},"
                     f" task_id={index_pickup_point.request.id}")
        raise
