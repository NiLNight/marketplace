import logging
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex, HashIndex
from django.core.exceptions import ValidationError
from django.db import models, transaction
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MinValueValidator, FileExtensionValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.core.utils import unique_slugify
from apps.core.models import TimeStampedModel
from django.contrib.postgres.search import SearchVectorField, SearchVector, Value

User = get_user_model()
logger = logging.getLogger(__name__)


class Category(MPTTModel):
    """Модель категории продуктов.

    Хранит иерархическую структуру категорий с названием, slug и описанием.

    Attributes:
        title: Название категории.
        slug: Уникальный slug для URL.
        description: Описание категории.
        parent: Родительская категория (если есть).
    """
    title = models.CharField(max_length=255, db_index=True, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        verbose_name='Родительская категория'
    )

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        """Метаданные модели Category."""
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        indexes = [
            models.Index(fields=['title']),
            HashIndex(fields=['slug']),
        ]

    @property
    def cached_children(self):
        """Кэшированные дочерние категории.

        Returns:
            QuerySet с дочерними категориями.
        """
        return getattr(self, '_cached_children', self.children.all())

    def __str__(self) -> str:
        """Возвращает строковое представление категории.

        Returns:
            Название категории.
        """
        return self.title

    def save(self, *args, **kwargs) -> None:
        """Сохраняет категорию с генерацией slug и логированием.

        Raises:
            ValidationError: Если данные категории некорректны.
        """
        user_id = 'anonymous'
        action = 'Creating' if self.pk is None else 'Updating'
        logger.info(f"{action} category with title={self.title}, user={user_id}")
        try:
            if not self.slug:
                self.slug = unique_slugify(self.title)
            super().save(*args, **kwargs)
            logger.info(f"Successfully {action.lower()} category {self.pk}, user={user_id}")
        except Exception as e:
            logger.error(f"Failed to {action.lower()} category: {str(e)}, user={user_id}")
            raise


class ProductManager(models.Manager):
    """Менеджер для модели Product."""

    def active(self):
        """Возвращает активные продукты."""
        return self.filter(is_active=True)

    def with_discount(self):
        """Возвращает продукты со скидкой."""
        return self.filter(discount__gt=0)


class Product(TimeStampedModel):
    """Модель продукта.

    Хранит информацию о продукте, включая название, цену, категорию и поисковый вектор.

    Attributes:
        title: Название продукта.
        slug: Уникальный slug для URL.
        description: Описание продукта.
        price: Цена продукта.
        discount: Скидка в процентах.
        stock: Количество на складе.
        category: Категория продукта.
        thumbnail: Изображение продукта.
        is_active: Статус активности.
        user: Пользователь, создавший продукт.
        search_vector: Вектор для полнотекстового поиска.
    """
    title = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, blank=True, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],  # Цена должна быть > 0
        verbose_name='Цена'
    )
    discount = models.DecimalField(
        default=0.0,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        verbose_name='Скидка'
    )
    stock = models.PositiveIntegerField(default=0, verbose_name='Запас')
    category = TreeForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True,
        verbose_name='Категория'
    )
    thumbnail = models.ImageField(
        upload_to='images/products/%Y/%m/%d',
        default='images/products/default.png',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        verbose_name='Миниатюра'
    )
    is_active = models.BooleanField(default=False, verbose_name='Активен')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Пользователь'
    )
    search_vector = SearchVectorField(null=True, blank=True, verbose_name='Поисковый вектор')
    popularity_score = models.FloatField(default=0.0, verbose_name='Популярность')
    objects = ProductManager()

    class Meta:
        """Метаданные модели Product."""
        ordering = ['-created']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['-created']),
            models.Index(fields=['is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['discount']),
            models.Index(fields=['stock']),
            models.Index(fields=['popularity_score']),
            models.Index(fields=['title', 'category'], name='title_category_idx'),
        ]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    @property
    def price_with_discount(self) -> Decimal:
        """Цена с учетом скидки.

        Returns:
            Decimal: Цена после применения скидки.
            Если цена или скидка равны None, возвращает None.
        """
        if self.price is None or self.discount is None:
            return None
        
        if isinstance(self.discount, float):
            discount = Decimal(str(self.discount))
        else:
            discount = self.discount
        return self.price * (Decimal('100') - discount) / Decimal('100')

    @property
    def in_stock(self) -> bool:
        """Проверяет наличие продукта на складе.

        Returns:
            True, если продукт в наличии.
        """
        return self.stock > 0

    def clean(self) -> None:
        """Проверяет данные продукта перед сохранением.

        Raises:
            ValidationError: Если цена со скидкой некорректна (меньше 0.01).
        """
        super().clean()
        if self.discount and self.price_with_discount < Decimal('0.01'):
            logger.warning(f"Invalid price with discount for product {self.title}")
            raise ValidationError(_("Цена со скидкой не может быть меньше 0.01"))

    def update_search_vector(self) -> None:
        """Обновляет поисковый вектор для полнотекстового поиска."""
        from django.db import connection
        if connection.vendor != 'postgresql':
            return
            
        category_title = self.category.title if self.category else ''
        self.search_vector = (
                SearchVector(Value(self.title), weight='A') +
                SearchVector(Value(self.description), weight='B') +
                SearchVector(Value(category_title), weight='C')
        )

    def save(self, *args, **kwargs) -> None:
        """Сохраняет продукт с генерацией slug и логированием.

        Raises:
            ValidationError: Если данные продукта некорректны.
        """
        user_id = self.user.id if self.user else 'anonymous'
        action = 'Creating' if self.pk is None else 'Updating'
        logger.info(f"{action} product with title={self.title}, user={user_id}")
        try:
            if not self.slug or self.title_changed():
                self.slug = unique_slugify(self.title)
                if Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                    self.slug = unique_slugify(self.title)

            # Пропускаем обновление поискового вектора при тестировании или если не PostgreSQL
            if not kwargs.pop('testing', False):
                try:
                    self.update_search_vector()
                except Exception as e:
                    logger.warning(f"Failed to update search vector: {str(e)}")
                    self.search_vector = None

            with transaction.atomic():
                super().save(*args, **kwargs)
            logger.info(f"Successfully {action.lower()} product {self.pk}, user={user_id}")
        except Exception as e:
            logger.error(f"Failed to {action.lower()} product: {str(e)}, user={user_id}")
            raise

    def title_changed(self) -> bool:
        """Проверяет, изменилось ли название продукта.

        Returns:
            True, если название изменилось.
        """
        if not self.pk:
            return True
        orig = Product.objects.get(pk=self.pk)
        return orig.title != self.title

    def should_update_elasticsearch(self) -> bool:
        """Проверяет, нужно ли обновлять документ в Elasticsearch.

        Returns:
            True, если изменились поля, влияющие на поиск.
        """
        if not self.pk:
            return True
        orig = Product.objects.get(pk=self.pk)
        return (
                orig.title != self.title or
                orig.description != self.description or
                orig.category_id != self.category_id or
                orig.price != self.price or
                orig.discount != self.discount or
                orig.is_active != self.is_active or
                orig.stock != self.stock
        )

    def __str__(self) -> str:
        """Возвращает строковое представление продукта.

        Returns:
            Название продукта.
        """
        return self.title
