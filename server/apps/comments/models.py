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
    """Модель для комментариев к отзывам.

    Хранит текст комментария, связь с отзывами и поддерживает иерархическую структуру для ответов.

    Атрибуты:
        review (ForeignKey): Отзыв, к которому относится комментарий.
        user (ForeignKey): Пользователь, создавший комментарий.
        text (TextField): Содержимое комментария.
        parent (TreeForeignKey): Родительский комментарий для ответов (опционально).
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пользователь'
    )
    text = models.TextField(verbose_name='Текст комментария')
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )

    class MPTTMeta:
        order_insertion_by = ['created']

    class Meta:
        """Метаданные модели Comment."""
        indexes = [models.Index(fields=['review', 'created'])]
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    @property
    def cached_children(self):
        """Кэшированные дочерние комментарии.

        Returns:
            QuerySet: Дочерние комментарии, кэшированные для оптимизации.
        """
        return getattr(self, '_cached_children', self.children.all())

    def __str__(self) -> str:
        """Строковое представление комментария.

        Returns:
            str: Название продукта и первые 50 символов текста комментария.
        """
        return f"{self.review.product.title}: {self.text[:50]}..."


class CommentLike(models.Model):
    """Модель для лайков комментариев.

    Хранит связь между пользователем и лайкнутым комментарием.

    Атрибуты:
        comment (ForeignKey): Комментарий, который лайкнули.
        user (ForeignKey): Пользователь, поставивший лайк.
        created (DateTimeField): Время создания лайка.
    """
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:

        unique_together = ('comment', 'user')
        verbose_name = 'Лайк комментария'
        verbose_name_plural = 'Лайки комментариев'
