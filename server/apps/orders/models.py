from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel

User = get_user_model()


class Delivery(models.Model):
    """Модель для хранения адресов доставки пользователя.

    Attributes:
        user (ForeignKey): Связь с пользователем, которому принадлежит адрес.
        address (CharField): Текст адреса доставки.
        cost (DecimalField): Стоимость доставки.
        is_primary (BooleanField): Флаг, указывающий, является ли адрес основным.
    """
    user = models.ForeignKey(
        User,
        related_name='deliveries',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Адрес'
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Стоимость'
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Основной адрес'
    )

    class Meta:
        """Метаданные модели Delivery."""
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'

    def __str__(self) -> str:
        """Строковое представление адреса доставки.

        Returns:
            str: Имя пользователя и адрес доставки.
        """
        return f"Адрес доставки для пользователя {self.user.username}"


class Order(TimeStampedModel):
    """Модель для хранения заказов пользователей.

    Attributes:
        user (ForeignKey): Связь с пользователем, создавшим заказ.
        status (CharField): Статус заказа (processing, shipped, delivered, cancelled).
        total_price (DecimalField): Общая стоимость заказа с учетом доставки.
        delivery (ForeignKey): Связь с адресом доставки.
    """
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        related_name='orders',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='processing',
        verbose_name='Статус'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Общая стоимость'
    )
    delivery = models.ForeignKey(
        Delivery,
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Доставка'
    )

    class Meta:
        """Метаданные модели Order."""
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created']),
        ]
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self) -> str:
        """Строковое представление заказа.

        Returns:
            str: ID заказа и имя пользователя.
        """
        return f"Заказ #{self.id} - {self.user.username}"
