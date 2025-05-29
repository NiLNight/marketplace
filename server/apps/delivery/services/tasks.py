from celery import shared_task
from apps.delivery.documents import PickupPointDocument
from apps.delivery.models import PickupPoint
from apps.delivery.exceptions import PickupPointNotFound
from elasticsearch_dsl.exceptions import ElasticsearchDslException
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(ConnectionError,), max_retries=3, retry_backoff=60)
def index_pickup_point(pickup_point_id: int):
    """
    Асинхронно индексирует пункт выдачи в Elasticsearch.

    Args:
        pickup_point_id (int): Идентификатор пункта выдачи.

    Returns:
        None: Метод не возвращает значения, только индексирует пункт выдачи.

    Raises:
        PickupPointNotFound: Если пункт выдачи не найден.
        ElasticsearchDslException: Если ошибка в Elasticsearch (повторяется до 3 раз с интервалом 60 секунд).
    """
    task_id = index_pickup_point.request.id
    try:
        pickup_point = PickupPoint.objects.get(pk=pickup_point_id)
        doc = PickupPointDocument(
            meta={'id': pickup_point.id},
            address=pickup_point.address,
            district=pickup_point.district or '',
            is_active=pickup_point.is_active,
            city={'id': pickup_point.city.id, 'name': pickup_point.city.name}
        )
        doc.instance = pickup_point
        doc.save()
        logger.info(
            f"Indexed pickup point ID={pickup_point_id}, task_id={task_id}"
        )
    except PickupPoint.DoesNotExist:
        logger.error(
            f"Pickup point not found ID={pickup_point_id}, task_id={task_id}"
        )
        raise PickupPointNotFound(
            detail=_("Пункт выдачи не найден"),
            code="not_found"
        )
    except ElasticsearchDslException as e:
        logger.error(
            f"Elasticsearch error indexing pickup point ID={pickup_point_id}: {str(e)}, "
            f"task_id={task_id}"
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error indexing pickup point ID={pickup_point_id}: {str(e)}, "
            f"task_id={task_id}"
        )
        raise


@shared_task(autoretry_for=(ConnectionError,), max_retries=3, retry_backoff=60)
def update_search_vector(pickup_point_id: int):
    """
    Асинхронно обновляет поисковый вектор для пункта выдачи.

    Args:
        pickup_point_id (int): Идентификатор пункта выдачи.

    Returns:
        None: Метод не возвращает значения, только обновляет поисковый вектор.

    Raises:
        PickupPointNotFound: Если пункт выдачи не найден (повторяется до 3 раз с интервалом 60 секунд).
    """
    task_id = update_search_vector.request.id
    try:
        pickup_point = PickupPoint.objects.get(pk=pickup_point_id)
        pickup_point.save()
        logger.info(
            f"Updated search_vector for pickup point ID={pickup_point_id}, task_id={task_id}"
        )
    except PickupPoint.DoesNotExist:
        logger.error(
            f"Pickup point not found for search_vector update ID={pickup_point_id}, task_id={task_id}"
        )
        raise PickupPointNotFound(
            detail=_("Пункт выдачи не найден"),
            code="not_found"
        )
