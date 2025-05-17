from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.contrib.postgres.search import SearchVectorField, SearchVector, Value
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class City(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название города'
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Delivery(models.Model):
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
        validators=[MinLengthValidator(5, message="Адрес должен содержать не менее 5 символов")],
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
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'

    def __str__(self) -> str:
        return f"Адрес доставки для пользователя {self.user.username}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            Delivery.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        self.full_clean()
        super().save(*args, **kwargs)


class PickupPoint(models.Model):
    city = models.ForeignKey(
        City,
        related_name='pickup_points',
        on_delete=models.CASCADE,
        verbose_name='Город'
    )
    address = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(5, message="Адрес должен содержать не менее 5 символов")],
        verbose_name='Адрес'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    search_vector = SearchVectorField(null=True, blank=True, verbose_name='Поисковый вектор')

    class Meta:
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['search_vector']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['city', 'address'], name='unique_city_address')
        ]
        verbose_name = 'Пункт выдачи'
        verbose_name_plural = 'Пункты выдачи'

    def __str__(self) -> str:
        return f"{self.city.name}, {self.address}"

    def save(self, *args, **kwargs):
        city_name = self.city.name if self.city else ''
        self.search_vector = (
                SearchVector(Value(self.address), weight='A', config='russian') +
                SearchVector(Value(city_name), weight='B', config='russian')
        )
        self.full_clean()
        super().save(*args, **kwargs)
