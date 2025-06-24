from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
import logging

from apps.orders.models import Order
from django.contrib.auth import get_user_model
from apps.products.models import Product

User = get_user_model()
logger = logging.getLogger(__name__)


class OrderItem(models.Model):
    """Модель для хранения элементов корзины или заказа.

    Представляет товар, добавленный пользователем в корзину или включенный в заказ.
    Хранит информацию о пользователе, товаре, количестве и связи с заказом.

    Attributes:
        order: Заказ, к которому относится элемент (опционально).
        user: Пользователь, добавивший элемент в корзину (опционально).
        product: Товар, связанный с элементом.
        quantity: Количество товара (от 1 до 20).
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items',
        null=True,
        blank=True,
        verbose_name='Заказ'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name='Количество'
    )

    class Meta:
        """Метаданные модели OrderItem.

        Определяет уникальные ограничения, индексы и отображаемые названия.
        """
        constraints = [
            # Уникальность товара в корзине для пользователя (order is null)
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=Q(order__isnull=True),
                name='unique_cart_product',
                violation_error_message='Товар уже находится в корзине пользователя.'
            ),
            # Уникальность товара в заказе (order is not null)
            models.UniqueConstraint(
                fields=['order', 'product'],
                condition=Q(order__isnull=False),
                name='unique_order_product',
                violation_error_message='Товар уже включен в заказ.'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'product'], name='idx_user_product'),
            models.Index(fields=['order', 'product'], name='idx_order_product'),
        ]
        verbose_name = 'Предмет заказа/корзины'
        verbose_name_plural = 'Предметы заказа/корзины'

    def __str__(self) -> str:
        """Строковое представление элемента корзины или заказа.

        Returns:
            str: Количество и название товара.

        Raises:
            AttributeError: Если product или его title недоступны из-за проблем с базой данных.
        """
        return f"{self.quantity} x {self.product.title}"

    def clean(self) -> None:
        """Валидация данных элемента перед сохранением.

        Проверяет, что элемент привязан либо к пользователю (корзина), либо к заказу,
        но не к обоим одновременно.

        Returns:
            None: Функция ничего не возвращает.

        Raises:
            ValidationError: Если элемент одновременно привязан к пользователю и заказу
                            или не привязан ни к одному из них.
        """
        if self.order is not None and self.user is not None:
            logger.warning(f"Invalid OrderItem: tied to both user and order, item_id={self.id}")
            raise ValidationError("Элемент не может одновременно принадлежать пользователю (корзина) и заказу.")
        if self.order is None and self.user is None:
            logger.warning(f"Invalid OrderItem: not tied to user or order, item_id={self.id}")
            raise ValidationError("Элемент должен быть привязан либо к пользователю, либо к заказу.")
