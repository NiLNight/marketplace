import logging
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.contrib.postgres.search import SearchVectorField, SearchVector, Value
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class City(models.Model):
    """
    Модель для хранения информации о городах.

    Attributes:
        name (CharField): Название города.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Название")
    )

    class Meta:
        ordering = ['name']
        verbose_name = _("Город")
        verbose_name_plural = _("Города")

    def __str__(self) -> str:
        """
        Возвращает строковое представление города.

        Returns:
            str: Название города.
        """
        return self.name

    def clean(self):
        """
        Проверяет корректность данных перед сохранением.

        Raises:
            ValidationError: Если название города некорректно.
        """
        if not self.name or not self.name.strip():
            raise ValidationError(_("Название города не может быть пустым"))

    def save(self, *args, **kwargs):
        """
        Сохраняет город с предварительной валидацией.

        Raises:
            ValidationError: Если данные некорректны.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class PickupPoint(models.Model):
    """
    Модель для хранения информации о пунктах выдачи.

    Attributes:
        city (ForeignKey): Связь с городом.
        address (CharField): Адрес пункта выдачи.
        district (CharField): Район (опционально).
        is_active (BooleanField): Статус активности.
        search_vector (SearchVectorField): Вектор для полнотекстового поиска.
    """
    city = models.ForeignKey(
        City,
        related_name='pickup_points',
        on_delete=models.CASCADE,
        verbose_name=_("Город")
    )
    address = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(5, message=_("Адрес должен содержать не менее 5 символов"))],
        verbose_name=_("Адрес")
    )
    district = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Район")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )
    search_vector = SearchVectorField(
        null=True,
        blank=True,
        verbose_name=_("Поисковый вектор")
    )

    class Meta:
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['search_vector']),
            models.Index(fields=['district']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['city', 'address'], name='unique_city_address')
        ]
        verbose_name = _("Пункт выдачи")
        verbose_name_plural = _("Пункты выдачи")

    def __str__(self) -> str:
        """
        Возвращает строковое представление пункта выдачи.

        Returns:
            str: Город и адрес пункта выдачи.
        """
        return f"{self.city.name}, {self.address}"

    def clean(self):
        """
        Проверяет корректность данных перед сохранением.

        Raises:
            ValidationError: Если город отсутствует или адрес некорректен.
        """
        if not self.city:
            raise ValidationError(_("Город не может быть пустым"))
        if not self._state.adding:
            try:
                current = PickupPoint.objects.get(pk=self.pk)
                if self.is_active != current.is_active:
                    raise ValidationError(_("Изменение статуса активности запрещено через модель"))
            except PickupPoint.DoesNotExist:
                logger.warning(f"Pickup point ID={self.pk} not found during clean")
                # Пропускаем, так как объект мог быть удален

    def save(self, *args, **kwargs):
        """
        Сохраняет пункт выдачи с обновлением поискового вектора в транзакции.

        Raises:
            ValidationError: Если данные некорректны.
        """
        with transaction.atomic():
            self.full_clean()
            city_name = self.city.name
            district_name = self.district or ''
            self.search_vector = (
                    SearchVector(Value(self.address), weight='A', config='russian') +
                    SearchVector(Value(city_name), weight='B', config='russian') +
                    SearchVector(Value(district_name), weight='B', config='russian')
            )
            super().save(*args, **kwargs)
