from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
from apps.delivery.models import Delivery, PickupPoint

User = get_user_model()


class Order(TimeStampedModel):
    """Модель для хранения заказов пользователей.

    Attributes:
        user (ForeignKey): Связь с пользователем, создавшим заказ.
        status (CharField): Статус заказа (processing, shipped, delivered, cancelled).
        total_price (DecimalField): Общая стоимость заказа с учетом доставки или самовывоза.
        delivery (ForeignKey): Связь с адресом доставки (может быть null).
        pickup_point (ForeignKey): Связь с пунктом выдачи (может быть null).
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
        blank=True,
        verbose_name='Доставка'
    )
    pickup_point = models.ForeignKey(
        PickupPoint,
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пункт выдачи'
    )

    class Meta:
        """Метаданные модели Order."""
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(delivery__isnull=True, pickup_point__isnull=True),
                name='either_delivery_or_pickup_point'
            ),
        ]
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self) -> str:
        """Строковое представление заказа.

        Returns:
            str: ID заказа и имя пользователя.
        """
        return f"Заказ #{self.id} - {self.user.username}"

    def clean(self):
        """Проверяет корректность данных перед сохранением.

        Raises:
            ValidationError: Если не указаны ни доставка, ни пункт выдачи, или указаны оба.
        """
        if self.delivery and self.pickup_point:
            raise ValidationError("Нельзя указать и доставку, и пункт выдачи одновременно.")
        if not self.delivery and not self.pickup_point:
            raise ValidationError("Необходимо указать либо доставку, либо пункт выдачи.")

    def save(self, *args, **kwargs):
        """Сохраняет объект с автоматической проверкой.

        Вызывает full_clean() для валидации перед сохранением.
        """
        self.full_clean()
        super().save(*args, **kwargs)
