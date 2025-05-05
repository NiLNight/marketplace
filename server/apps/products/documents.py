import logging
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from apps.products.models import Product

logger = logging.getLogger(__name__)


@registry.register_document
class ProductDocument(Document):
    title = fields.TextField(analyzer='standard', fields={'raw': fields.KeywordField()})
    description = fields.TextField(analyzer='standard')
    price = fields.FloatField()
    discount = fields.FloatField()
    price_with_discount = fields.FloatField()
    stock = fields.IntegerField()
    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'title': fields.TextField(),
        'slug': fields.KeywordField(),
    })
    is_active = fields.BooleanField()

    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        model = Product
        fields = [
            'id',
        ]

    def prepare_price(self, instance):
        """Преобразует Decimal в float для price."""
        return float(instance.price)

    def prepare_discount(self, instance):
        """Преобразует Decimal в float для discount."""
        return float(instance.discount)

    def prepare_price_with_discount(self, instance):
        """Вычисляет цену с учётом скидки."""
        return float(instance.price_with_discount)

    def prepare_category(self, instance):
        """Подготовка данных категории для индекса."""
        try:
            return {
                'id': instance.category.id,
                'title': instance.category.title,
                'slug': instance.category.slug,
            } if instance.category else {}
        except Exception as e:
            logger.error(f"Failed to prepare category for product {instance.id}: {str(e)}")
            return {}

    def save(self, **kwargs):
        """Логирование сохранения документа."""
        logger.info(f"Saving product document with id={self.id}")
        try:
            super().save(**kwargs)
            logger.info(f"Successfully saved product document {self.id}")
        except Exception as e:
            logger.error(f"Failed to save product document {self.id}: {str(e)}")
            raise
