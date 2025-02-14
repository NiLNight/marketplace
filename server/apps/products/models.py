from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import FileExtensionValidator

from apps.services.utils import unique_slugify
from apps.users.models import User
from apps.core.models import TimeStampedModel


class CategoryManager(models.Manager):
    def with_products(self):
        return self.prefetch_related('products')


class Category(MPTTModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    objects = CategoryManager()

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        indexes = [
            models.Index(fields=['title', 'slug']),
        ]

    def get_absolute_url(self):
        """
        Получаем прямую ссылку на категорию
        """
        return reverse('blog:post_by_category', kwargs={'slug': self.slug})

    def __str__(self):
        """
        Возвращение заголовка категории
        """
        return self.title


class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def with_discount(self):
        return self.filter(discount__gt=0)


class Product(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField()
    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    discount = models.DecimalField(default=0.00, max_digits=4, decimal_places=2,
                                   null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    category = TreeForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    thumbnail = models.ImageField(
        upload_to='images/products/%Y/%m/%d',
        default='images/avatars/default.png',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'gif'])]
    )
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    objects = ProductManager()

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['price', '-created', 'is_active']),
        ]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    @property
    def price_with_discount(self):
        return self.price * (1 - self.discount / 100) if self.discount else self.price

    def is_in_stock(self):
        return self.stock > 0

    def save(self, *args, **kwargs):
        """
        При сохранении генерируем слаг и проверяем на уникальность
        """
        self.slug = unique_slugify(self.title)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
