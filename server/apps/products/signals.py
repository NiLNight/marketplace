import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.products.models import Product
from apps.products.documents import ProductDocument

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def update_product_in_elasticsearch(sender, instance, created, **kwargs):
    """Обновляет или создаёт документ в Elasticsearch при сохранении продукта."""
    user_id = instance.user.id if instance.user else 'anonymous'
    action = 'Creating' if created else 'Updating'
    logger.info(
        f"{action} product in Elasticsearch with title={instance.title}, user={user_id}, is_active={instance.is_active}")
    try:
        if instance.should_update_elasticsearch():
            ProductDocument().update(instance)
            logger.info(f"Successfully {action.lower()} product in Elasticsearch {instance.id}, user={user_id}")
        else:
            logger.info(f"Skipping Elasticsearch update for product {instance.id}, user={user_id}")
    except Exception as e:
        logger.exception(f"Failed to {action.lower()} product in Elasticsearch {instance.id}: {str(e)}, user={user_id}")


@receiver(post_delete, sender=Product)
def delete_product_from_elasticsearch(sender, instance, **kwargs):
    """Удаляет документ из Elasticsearch при удалении продукта."""
    user_id = instance.user.id if instance.user else 'anonymous'
    logger.info(f"Deleting product from Elasticsearch with title={instance.title}, user={user_id}")
    try:
        ProductDocument().delete(instance)
        logger.info(f"Successfully deleted product from Elasticsearch {instance.id}, user={user_id}")
    except Exception as e:
        logger.exception(f"Failed to delete product from Elasticsearch {instance.id}: {str(e)}, user={user_id}")
