import logging
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.exceptions import ElasticsearchDslException
from apps.delivery.models import PickupPoint, City
from apps.delivery.exceptions import ElasticsearchUnavailable
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


@registry.register_document
class PickupPointDocument(Document):
    """
    Документ Elasticsearch для модели PickupPoint.

    Используется для индексации пунктов выдачи в поисковом движке.
    """
    address = fields.TextField(analyzer='standard', fields={'raw': fields.KeywordField()})
    district = fields.TextField(analyzer='standard', fields={'raw': fields.KeywordField()})
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
        """
        Возвращает оптимизированный запрос для индексации.

        Returns:
            QuerySet: QuerySet с выбранными связанными данными.
        """
        logger.info("Action=GetDocumentQueryset")
        return super().get_queryset().select_related('city')

    def prepare_city(self, instance):
        """
        Подготавливает данные города для индексации.

        Args:
            instance (PickupPoint): Экземпляр модели пункта выдачи.

        Returns:
            dict: Данные города.
        """
        try:
            if not instance.city:
                logger.warning(
                    f"No city associated with pickup point ID={instance.id}, "
                    f"IP={getattr(self, 'request', {}).get('REMOTE_ADDR', 'unknown')}"
                )
                return {}
            return {
                'id': instance.city.id,
                'name': instance.city.name,
            }
        except Exception as e:
            logger.error(
                f"Failed to prepare city for pickup point ID={instance.id}: {str(e)}, "
                f"IP={getattr(self, 'request', {}).get('REMOTE_ADDR', 'unknown')}"
            )
            return {}

    def prepare_district(self, instance):
        """
        Подготавливает данные района для индексации.

        Args:
            instance (PickupPoint): Экземпляр модели пункта выдачи.

        Returns:
            str: Название района или пустая строка.
        """
        try:
            return instance.district or ''
        except AttributeError as e:
            logger.error(
                f"Failed to access district for pickup point ID={instance.id}: {str(e)}, "
                f"IP={getattr(self, 'request', {}).get('REMOTE_ADDR', 'unknown')}"
            )
            return ''

    def save(self, **kwargs):
        """
        Сохраняет документ в Elasticsearch.

        Args:
            kwargs (dict): Дополнительные аргументы.

        Raises:
            ElasticsearchUnavailable: Если Elasticsearch недоступен.
        """
        task_id = getattr(self, 'task_id', 'unknown')
        logger.info(f"Action=SaveDocument ID={self.id}, task_id={task_id}")
        try:
            super().save(**kwargs)
            logger.info(
                f"Successfully saved pickup point document ID={self.id}, task_id={task_id}, "
                f"IP={getattr(self, 'request', {}).get('REMOTE_ADDR', 'unknown')}"
            )
        except ElasticsearchDslException as e:
            logger.error(
                f"Elasticsearch error saving pickup point document ID={self.id}: {str(e)}, "
                f"task_id={task_id}, IP={getattr(self, 'request', {}).get('REMOTE_ADDR', 'unknown')}"
            )
            raise ElasticsearchUnavailable(
                detail=_("Сервис поиска временно недоступен"),
                code="service_unavailable"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error saving pickup point document ID={self.id}: {str(e)}, "
                f"task_id={task_id}, IP={getattr(self, 'request', {}).get('REMOTE_ADDR', 'unknown')}"
            )
            raise
