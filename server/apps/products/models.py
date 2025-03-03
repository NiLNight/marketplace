from decimal import Decimal
from django.contrib.postgres.indexes import GinIndex, HashIndex
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import MinValueValidator

from django.utils.translation import gettext_lazy as _

from apps.core.utils import unique_slugify
from apps.users.models import User
from apps.core.models import TimeStampedModel
from django.contrib.postgres.search import SearchVectorField, SearchVector


class Category(MPTTModel):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
    )

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        indexes = [
            models.Index(fields=['title']),
            HashIndex(fields=['slug']),
        ]

    @property
    def cached_children(self):
        return getattr(self, '_cached_children', self.children.all())

    def __str__(self):
        return self.title


class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def with_discount(self):
        return self.filter(discount__gt=0)


class Product(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal(0.00))])
    discount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = TreeForeignKey(Category, on_delete=models.CASCADE, related_name='products', db_index=True)
    thumbnail = models.ImageField(
        upload_to='images/products/%Y/%m/%d',
        default='images/products/default.png',
        blank=True,
        editable=False
    )
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    search_vector = SearchVectorField(null=True, blank=True)
    objects = ProductManager()

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['-created']),
            models.Index(fields=['is_active']),
            GinIndex(fields=['search_vector']),
            models.Index(fields=['price']),
        ]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'category'],
                name='unique_product_category'
            )
        ]

    @property
    def price_with_discount(self):
        return self.price * (100 - self.discount) / 100

    @property
    def in_stock(self):
        return self.stock > 0

    def clean(self):
        super().clean()
        if self.discount and self.price_with_discount < Decimal('0.01'):
            raise ValidationError(_("Цена со скидкой не может быть меньше 0.01"))

    def save(self, *args, **kwargs):
        if not self.slug or self.title_changed():
            self.slug = unique_slugify(self.title)
            if Product.objects.filter(slug=self.slug).exists():
                self.slug = unique_slugify(self.title)

        with transaction.atomic():
            super().save(*args, **kwargs)

    def title_changed(self):
        if not self.pk:
            return True
        orig = Product.objects.get(pk=self.pk)
        return orig.title != self.title

    def __str__(self):
        return self.title


@receiver(post_save, sender=Product)
def update_search_vector(sender, instance, created, update_fields, **kwargs):
    if created or 'title' in (update_fields or []) or 'description' in (update_fields or []):
        instance.search_vector = (
                SearchVector('title', weight='A') +
                SearchVector('description', weight='B')
        )
