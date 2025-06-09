import logging
from celery import shared_task

from apps.core.services.cache_services import CacheService
from apps.products.models import Product
from apps.products.documents import ProductDocument
from apps.products.utils import calculate_popularity_score

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_elasticsearch_task(self, product_id: int, delete: bool = False) -> None:
    """Обновляет или удаляет данные продукта в Elasticsearch.

    Args:
        self: Экземпляр задачи Celery.
        product_id (int): Идентификатор продукта для обновления.
        delete (bool): Флаг, указывающий на необходимость удаления документа.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        Product.DoesNotExist: Если продукт не найден.
        Exception: Если обновление в Elasticsearch не удалось.
    """
    try:
        if delete:
            # При удалении продукта удаляем его документ из Elasticsearch
            doc = ProductDocument.get(id=product_id)
            doc.delete()
            logger.info(f"Deleted product {product_id} from Elasticsearch")
            return

        # При обновлении или создании
        product = Product.objects.get(pk=product_id)
        if product.should_update_elasticsearch():
            if product.is_active:
                doc = ProductDocument.from_instance(product)
                doc.save()
                logger.info(f"Updated Elasticsearch for product {product_id}")
            else:
                # Если продукт неактивен, удаляем его из индекса
                doc = ProductDocument.get(id=product_id)
                doc.delete()
                logger.info(f"Removed inactive product {product_id} from Elasticsearch")

    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found")
    except Exception as e:
        logger.error(f"Failed to update Elasticsearch for product {product_id}: {str(e)}")
        # Повторяем задачу при ошибке
        raise self.retry(exc=e)


@shared_task
def update_popularity_score(product_id):
    """Обновляет показатель популярности продукта.

    Args:
        product_id (int): Идентификатор продукта для обновления.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        Product.DoesNotExist: Если продукт не найден.
        Exception: Если обновление популярности или инвалидация кэша не удались.
    """
    logger.info(f"Starting update_popularity_score for product {product_id}")
    try:
        product = Product.objects.get(pk=product_id)
        new_score = calculate_popularity_score(product)
        logger.debug(f"Calculated popularity_score={new_score} for product {product_id}")
        product.popularity_score = new_score
        product.save(update_fields=['popularity_score'])
        # Инвалидация кэша
        try:
            CacheService.invalidate_cache(prefix="product_list")
            CacheService.invalidate_cache(prefix="product_detail", pk=product.id)
            logger.info(f"Invalidated cache for product {product_id} (product_detail, product_list)")
        except Exception as cache_error:
            logger.error(f"Failed to invalidate cache for product {product_id}: {str(cache_error)}")

        logger.info(f"Updated popularity_score for product {product_id}")
    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found")
    except Exception as e:
        logger.error(f"Failed to update popularity_score for product {product_id}: {str(e)}")
