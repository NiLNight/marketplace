from django.contrib.auth import get_user_model
from django.db import models
from apps.core.models import TimeStampedModel
from apps.products.models import Product
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class WishlistItem(TimeStampedModel):
    """Модель элемента списка желаний.

    Хранит информацию о товаре, добавленном в список желаний пользователем.

    Attributes:
        user: Пользователь, добавивший товар в список желаний (опционально).
        product: Товар, добавленный в список желаний.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        related_name='wishlist_items',
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )

    class Meta:
        """Метаданные модели WishlistItem."""
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=models.Q(user__isnull=False),
                name='unique_wishlist_product'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'product']),
        ]
        verbose_name = 'Элемент списка желаний'
        verbose_name_plural = 'Элементы списка желаний'

    def __str__(self):
        """Строковое представление элемента списка желаний.

        Returns:
            str: Название товара и ID пользователя.

        Raises:
            AttributeError: Если product.title или user.username недоступны из-за проблем с базой данных.
        """
        return f"{self.product.title} в списке желаний {self.user.username if self.user else 'гостя'}"