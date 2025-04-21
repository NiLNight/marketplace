from django.contrib.auth import get_user_model
from django.db import models
from apps.core.models import TimeStampedModel
from apps.products.models import Product

User = get_user_model()


class WishlistItem(TimeStampedModel):
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
