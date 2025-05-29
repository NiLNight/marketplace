from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
from apps.delivery.models import PickupPoint
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Order(TimeStampedModel):
    """
    Модель для хранения заказов пользователей.

    Attributes:
        user (ForeignKey): Связь с пользователем, создавшим заказ.
        status (CharField): Статус заказа (processing, shipped, delivered, cancelled).
        total_price (DecimalField): Общая стоимость заказа.
        pickup_point (ForeignKey): Связь с пунктом выдачи (обязательное поле).
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
    pickup_point = models.ForeignKey(
        PickupPoint,
        related_name='orders',
        on_delete=models.PROTECT,
        verbose_name='Пункт выдачи'
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
        """
        Строковое представление заказа.

        Returns:
            str: ID заказа и имя пользователя.

        Raises:
            AttributeError: Если user.username недоступен из-за проблем с базой данных.
        """
        return f"Заказ #{self.id} - {self.user.username}"

    def clean(self):
        """
        Проверяет корректность данных перед сохранением.

        Убеждается, что total_price не отрицателен и pickup_point активен.

        Returns:
            None: Метод не возвращает значения, только проверяет данные.

        Raises:
            ValidationError: Если данные некорректны (total_price отрицателен или pickup_point неактивен).
        """
        if self.total_price < 0:
            raise ValidationError(_("Общая стоимость не может быть отрицательной"))
        if self.pickup_point and not self.pickup_point.is_active:
            raise ValidationError(_("Пункт выдачи неактивен"))

    def save(self, *args, **kwargs):
        """
        Сохраняет объект с автоматической проверкой.

        Вызывает full_clean() для валидации перед сохранением.

        Args:
            *args: Позиционные аргументы для метода save.
            **kwargs: Именованные аргументы для метода save.

        Returns:
            None: Метод сохраняет объект в базе данных.

        Raises:
            ValidationError: Если данные не прошли валидацию.
        """
        self.full_clean()
        super().save(*args, **kwargs)