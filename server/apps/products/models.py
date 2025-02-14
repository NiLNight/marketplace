from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from apps.users.models import User
from apps.core.models import TimeStampedModel


class CategoryManager(models.Manager):
    def with_products(self):
        return self.prefetch_related('products')


class Category(MPTTModel):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
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
