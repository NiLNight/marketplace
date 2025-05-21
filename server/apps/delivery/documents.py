import logging
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.exceptions import ElasticsearchDslException
from apps.delivery.models import PickupPoint, City

logger = logging.getLogger(__name__)


@registry.register_document
class PickupPointDocument(Document):
    """Документ Elasticsearch для модели PickupPoint."""
    address = fields.TextField(analyzer='standard', fields={'raw': fields.KeywordField()})
    city = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(analyzer='standard'),
    })
    is_active = fields.BooleanField()

    class Index:
        name = 'pickup_points'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        model = PickupPoint
        fields = ['id']
        related_models = [City]

    def get_queryset(self):
        """Возвращает оптимизированный запрос для индексации."""
        return super().get_queryset().select_related('city')

    def prepare_city(self, instance):
        """Подготавливает данные города для индексации."""
        try:
            if not instance.city:
                logger.warning(f"No city associated with pickup point {instance.id}")
                return {}
            return {
                'id': instance.city.id,
                'name': instance.city.name,
            }
        except Exception as e:
            logger.error(f"Failed to prepare city for pickup point {instance.id}: {str(e)}")
            return {}

    def save(self, **kwargs):
        """Сохраняет документ в Elasticsearch с логированием."""
        logger.info(f"Saving pickup point document with id={self.id}")
        try:
            super().save(**kwargs)
            logger.info(f"Successfully saved pickup point document {self.id}")
        except ElasticsearchDslException as e:
            logger.error(f"Elasticsearch error saving pickup point document {self.id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving pickup point document {self.id}: {str(e)}")
            raise
