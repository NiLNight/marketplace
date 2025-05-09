import logging
from celery import shared_task

from apps.core.services.cache_services import CacheService
from apps.products.models import Product
from apps.products.documents import ProductDocument
from apps.products.utils import calculate_popularity_score

logger = logging.getLogger(__name__)


@shared_task
def update_elasticsearch_task(product_id):
    try:
        product = Product.objects.get(pk=product_id)
        if product.should_update_elasticsearch():
            if product.is_active:
                ProductDocument().update(product)
            else:
                ProductDocument().delete(product)
            logger.info(f"Updated Elasticsearch for product {product_id}")
    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found")
    except Exception as e:
        logger.error(f"Failed to update Elasticsearch for product {product_id}: {str(e)}")


@shared_task
def update_popularity_score(product_id):
    logger.info(f"Starting update_popularity_score for product {product_id}")
    try:
        product = Product.objects.get(pk=product_id)
        new_score = calculate_popularity_score(product)
        logger.debug(f"Calculated popularity_score={new_score} for product {product_id}")
        product.popularity_score = new_score
        product.save(update_fields=['popularity_score'])

        # Инвалидация кэша
        try:
            CacheService.invalidate_cache(prefix="product_detail", pk=product.id)
            CacheService.invalidate_cache(prefix="product_list")
            logger.info(f"Invalidated cache for product {product_id} (product_detail, product_list)")
        except Exception as cache_error:
            logger.error(f"Failed to invalidate cache for product {product_id}: {str(cache_error)}")

        logger.info(f"Updated popularity_score for product {product_id}")
    except Product.DoesNotExist:
        logger.warning(f"Product {product_id} not found")
    except Exception as e:
        logger.error(f"Failed to update popularity_score for product {product_id}: {str(e)}")
