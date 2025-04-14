from django.contrib.auth.models import User
from django.db import models
from apps.core.models import TimeStampedModel
from mptt.models import MPTTModel, TreeForeignKey

from apps.products.models import Product


class Review(TimeStampedModel):
    """
    Модель рейтинга: От 1 до 5
    """
    values = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings', verbose_name='Запись')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь')
    value = models.BigIntegerField(default=0, choices=values, verbose_name='Оценка')
    text = models.TextField(blank=True, null=True, verbose_name='Текст отзыва')
    image = models.ImageField(upload_to='images/reviews/%Y/%m/%d', blank=True, null=True)

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
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['created']

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f"{self.review.product.title}: {self.text[:50]}..."


class ReviewLike(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')
