from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.postgres.search import SearchVectorField, SearchVector, Value
from django.utils.translation import gettext_lazy as _


class City(models.Model):
    """
    Модель для хранения городов.

    Attributes:
        name (CharField): Название города.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Название')
    )

    class Meta:
        """Метаданные модели City."""
        ordering = ['name']  # Сортировка по имени города
        verbose_name = _('Город')
        verbose_name_plural = _('Города')

    def __str__(self) -> str:
        """
        Строковое представление города.

        Returns:
            str: Название города.
        """
        return self.name

    def save(self, *args, **kwargs):
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
    district = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Район'
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
        if not self.city:
            raise ValidationError("Город не может быть пустым")
        city_name = self.city.name
        district_name = self.district or ''
        self.search_vector = (
                SearchVector(Value(self.address), weight='A', config='russian') +
                SearchVector(Value(city_name), weight='B', config='russian') +
                SearchVector(Value(district_name), weight='B', config='russian')
        )
        self.full_clean()
        super().save(*args, **kwargs)
