from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class City(models.Model):
    """Модель для хранения городов.

    Attributes:
        name (CharField): Название города.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название города'
    )

    class Meta:
        """Метаданные модели City."""
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self) -> str:
        """Строковое представление города.

        Returns:
            str: Название города.
        """
        return self.name


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


class PickupPoint(models.Model):
    """Модель для хранения пунктов выдачи.

    Attributes:
        city (ForeignKey): Связь с городом, в котором находится пункт выдачи.
        address (CharField): Адрес пункта выдачи.
        is_active (BooleanField): Флаг, указывающий, активен ли пункт выдачи.
    """
    city = models.ForeignKey(
        City,
        related_name='pickup_points',
        on_delete=models.PROTECT,
        verbose_name='Город'
    )
    address = models.CharField(
        max_length=255,
        verbose_name='Адрес'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    class Meta:
        """Метаданные модели PickupPoint."""
        indexes = [
            models.Index(fields=['city', 'is_active']),
        ]
        verbose_name = 'Пункт выдачи'
        verbose_name_plural = 'Пункты выдачи'

    def __str__(self) -> str:
        """Строковое представление пункта выдачи.

        Returns:
            str: Город и адрес пункта выдачи.
        """
        return f"{self.city.name}, {self.address}"
