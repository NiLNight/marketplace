import logging

from django.contrib.auth import get_user_model
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from apps.core.models import TimeStampedModel
from apps.reviews.models import Review

User = get_user_model()
logger = logging.getLogger(__name__)


class Comment(MPTTModel, TimeStampedModel):
    """Модель комментария к отзыву.

    Хранит текст комментария, связь с отзывом и иерархию комментариев.
    """
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
        """Кэшированные дочерние комментарии."""
        return getattr(self, '_cached_children', self.children.all())

    def __str__(self) -> str:
        """Строковое представление комментария.

        Returns:
            str: Название продукта и первые 50 символов текста.
        """
        return f"{self.review.product.title}: {self.text[:50]}..."

    def save(self, *args, **kwargs) -> None:
        """Сохраняет комментарий с логированием.

        Raises:
            ValidationError: Если валидация не пройдена.
        """
        user_id = self.user.id if self.user else 'anonymous'
        if self.pk is None:
            logger.info(f"Creating comment for review={self.review.id}, user={user_id}")
        else:
            logger.info(f"Updating comment {self.pk}, user={user_id}")
        super().save(*args, **kwargs)


class CommentLike(models.Model):
    """Модель лайка для комментария."""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')
