from django.contrib.auth.models import User
from django.db import models
from apps.core.models import TimeStampedModel
from mptt.models import MPTTModel, TreeForeignKey

from apps.products.models import Product


class Review(TimeStampedModel):
    """
    Модель рейтинга: От 1 до 5
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings', verbose_name='Запись')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь')
    value = models.BigIntegerField(default=0, choices=[(str(i) for i in range(1, 6))], verbose_name='Оценка')
    text = models.TextField(blank=True, null=True, verbose_name='Текст отзыва')
    ip_address = models.GenericIPAddressField(verbose_name='IP Адрес')

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created']
        indexes = [models.Index(fields=['-created', 'value'])]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"{self.product.title}: {self.value} ({self.user.username})"


class Comment(MPTTModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    class MPTTMeta:
        order_insertion_by = ['create_time']

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f"{self.review.product.title}: {self.text[:50]}..."
