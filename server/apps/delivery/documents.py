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

    Attributes:
        address: Текстовое поле для адреса с анализатором standard.
        district: Текстовое поле для района с анализатором standard.
        city: Объектное поле для данных города (id и name).
        is_active: Булево поле для статуса активности.
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

    def get_instances_from_related(self, related_instance):
        """
        Получает связанные экземпляры PickupPoint для обновления в Elasticsearch.

        Args:
            related_instance: Связанный объект (City).

        Returns:
            QuerySet: Набор связанных объектов PickupPoint.
        """
        if isinstance(related_instance, City):
            return related_instance.pickup_points.all()
        return []

    def get_queryset(self):
        """
        Получает QuerySet для индексации.

        Returns:
            QuerySet: Оптимизированный QuerySet с предзагрузкой связанных данных.
        """
        return super().get_queryset().select_related('city')

    def prepare_city(self, instance):
        """
        Подготавливает данные города для индексации.

        Args:
            instance (PickupPoint): Экземпляр модели пункта выдачи.

        Returns:
            dict: Данные города или пустой словарь, если город отсутствует.

        Raises:
            Exception: Если доступ к данным города не удался из-за проблем с базой данных.
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
            str: Название района или пустая строка, если район отсутствует.

        Raises:
            AttributeError: Если доступ к district не удался из-за проблем с базой данных.
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
            kwargs (dict): Дополнительные аргументы для метода save.

        Returns:
            None: Метод сохраняет документ в Elasticsearch.

        Raises:
            ElasticsearchUnavailable: Если Elasticsearch недоступен.
            Exception: Если произошла непредвиденная ошибка при сохранении документа.
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
