import logging
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.db.models import Avg, Count
from django.utils import timezone
from apps.products.models import Product

logger = logging.getLogger(__name__)


@registry.register_document
class ProductDocument(Document):
    """Документ Elasticsearch для модели Product.

    Определяет структуру и настройки индексации продуктов в Elasticsearch.
    """

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
    popularity_score = fields.FloatField()
    rating_avg = fields.FloatField()

    class Index:
        """Конфигурация индекса для Elasticsearch."""
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
        }

    class Django:
        """Сопоставление с моделью Django."""
        model = Product
        fields = [
            'id',
        ]

    def prepare_price(self, instance):
        """Преобразует Decimal в float для поля price.

        Args:
            instance: Экземпляр Product.

        Returns:
            Float-значение цены.
        """
        return float(instance.price)

    def prepare_discount(self, instance):
        """Преобразует Decimal в float для поля discount.

        Args:
            instance: Экземпляр Product.

        Returns:
            Float-значение скидки.
        """
        return float(instance.discount)

    def prepare_price_with_discount(self, instance):
        """Вычисляет цену с учётом скидки.

        Args:
            instance: Экземпляр Product.

        Returns:
            Float-значение цены с учётом скидки.
        """
        return float(instance.price_with_discount)

    def prepare_category(self, instance):
        """Подготавливает данные категории для индексации.

        Args:
            instance: Экземпляр Product.

        Returns:
            Словарь с данными категории или пустой словарь, если категория отсутствует.
        """
        try:
            return {
                'id': instance.category.id,
                'title': instance.category.title,
                'slug': instance.category.slug,
            } if instance.category else {}
        except Exception as e:
            logger.error(f"Failed to prepare category for product {instance.id}: {str(e)}")
            return {}

    def prepare_popularity_score(self, instance):
        """Вычисляет показатель популярности для индексации.

        Args:
            instance: Экземпляр Product.

        Returns:
            Float-значение показателя популярности.
        """
        try:
            purchase_count = instance.order_items.filter(order__isnull=False).count()
            review_count = instance.reviews.count()
            rating_avg = instance.reviews.aggregate(Avg('value'))['value__avg'] or 0.0
            days_since_created = (timezone.now() - instance.created).days + 1
            popularity_score = (
                    (purchase_count * 0.4) +
                    (review_count * 0.2) +
                    (rating_avg * 0.3) +
                    (1 / days_since_created * 0.1)
            )
            return float(popularity_score)
        except Exception as e:
            logger.error(f"Failed to prepare popularity_score for product {instance.id}: {str(e)}")
            return 0.0

    def prepare_rating_avg(self, instance):
        """Вычисляет средний рейтинг для индексации.

        Args:
            instance: Экземпляр Product.

        Returns:
            Float-значение среднего рейтинга.
        """
        try:
            rating_avg = instance.reviews.aggregate(Avg('value'))['value__avg'] or 0.0
            return float(rating_avg)
        except Exception as e:
            logger.error(f"Failed to prepare rating_avg for product {instance.id}: {str(e)}")
            return 0.0

    def save(self, **kwargs):
        """Сохраняет документ в Elasticsearch с логированием.

        Args:
            **kwargs: Дополнительные аргументы для операции сохранения.

        Raises:
            Exception: Если сохранение в Elasticsearch не удалось.
        """
        logger.info(f"Saving product document with id={self.id}")
        try:
            super().save(**kwargs)
            logger.info(f"Successfully saved product document {self.id}")
        except Exception as e:
            logger.error(f"Failed to save product document {self.id}: {str(e)}")
            raise
