import logging
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.db.models import Avg
from apps.products.models import Product
from apps.products.utils import calculate_popularity_score

logger = logging.getLogger(__name__)


@registry.register_document
class ProductDocument(Document):
    """Документ Elasticsearch для модели Product.

    Определяет структуру и настройки индексации продуктов в Elasticsearch.
    """

    title = fields.TextField(
        analyzer='standard',
        fields={
            'raw': fields.KeywordField(),
            'ngram': fields.TextField(analyzer='ngram_analyzer')
        }
    )
    description = fields.TextField(
        analyzer='standard',
        fields={
            'ngram': fields.TextField(analyzer='ngram_analyzer')
        }
    )
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
    created = fields.DateField()

    class Index:
        """Конфигурация индекса для Elasticsearch."""
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'analysis': {
                'analyzer': {
                    'ngram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'ngram_tokenizer',
                        'filter': ['lowercase']
                    }
                },
                'tokenizer': {
                    'ngram_tokenizer': {
                        'type': 'ngram',
                        'min_gram': 3,
                        'max_gram': 4,
                        'token_chars': ['letter', 'digit']
                    }
                }
            }
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
            float: Float-значение цены.
        """
        return float(instance.price)

    def prepare_discount(self, instance):
        """Преобразует Decimal в float для поля discount.

        Args:
            instance: Экземпляр Product.

        Returns:
            float: Float-значение скидки.
        """
        return float(instance.discount)

    def prepare_price_with_discount(self, instance):
        """Вычисляет цену с учётом скидки.

        Args:
            instance: Экземпляр Product.

        Returns:
            float: Float-значение цены с учётом скидки.
        """
        return float(instance.price_with_discount)

    def prepare_category(self, instance):
        """Подготавливает данные категории для индексации.

        Args:
            instance: Экземпляр Product.

        Returns:
            dict: Словарь с данными категории или пустой словарь, если категория отсутствует.
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
            float: Float-значение показателя популярности.
        """
        try:
            return calculate_popularity_score(instance)
        except Exception as e:
            logger.error(f"Failed to prepare popularity_score for product {instance.id}: {str(e)}")
            return 0.0

    def prepare_rating_avg(self, instance):
        """Вычисляет средний рейтинг для индексации.

        Args:
            instance: Экземпляр Product.

        Returns:
            float: Float-значение среднего рейтинга.
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

        Returns:
            None: Функция ничего не возвращает.

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
