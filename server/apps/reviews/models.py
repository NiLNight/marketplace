from django.contrib.auth.models import User
from django.db import models
from apps.core.models import TimeStampedModel
from mptt.models import MPTTModel, TreeForeignKey
from apps.products.models import Product


class Review(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='Продукт')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name='Пользователь')
    value = models.SmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name='Оценка')
    text = models.TextField(blank=True, verbose_name='Текст отзыва')
    image = models.ImageField(upload_to='images/reviews/%Y/%m/%d', blank=True, verbose_name='Изображение')

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created']
        indexes = [models.Index(fields=['product', '-created'])]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"{self.product.title}: {self.value} ({self.user.username})"


class Comment(MPTTModel, TimeStampedModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments', verbose_name='Отзыв')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='Пользователь')
    text = models.TextField(verbose_name='Текст комментария')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    class MPTTMeta:
        order_insertion_by = ['created']

    class Meta:
        indexes = [models.Index(fields=['review', 'created'])]
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    @property
    def cached_children(self):
        return getattr(self, '_cached_children', self.children.all())

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
