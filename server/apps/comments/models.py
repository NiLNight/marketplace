import logging
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from apps.core.models import TimeStampedModel, Like
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
        likes (GenericRelation): Связь с моделью лайков.
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
    likes = GenericRelation(
        Like,
        related_query_name='review',
        content_type_field='content_type',
        object_id_field='object_id'
    )
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

        Raises:
            Exception: Если произошла ошибка при получении дочерних комментариев из-за проблем с базой данных.
        """
        return getattr(self, '_cached_children', self.children.all())

    def __str__(self) -> str:
        """Строковое представление комментария.

        Returns:
            str: Название продукта и первые 50 символов текста комментария.
        """
        return f"{self.review.product.title}: {self.text[:50]}..."
