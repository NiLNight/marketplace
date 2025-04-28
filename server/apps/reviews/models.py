import logging
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import FileExtensionValidator
from django.db import models
from apps.core.models import TimeStampedModel, Like
from apps.products.models import Product
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class Review(TimeStampedModel):
    """Модель отзыва о продукте.

    Хранит информацию о продукте, пользователе, оценке, тексте и изображении отзыва.

    Атрибуты:
        product (ForeignKey): Продукт, к которому относится отзыв.
        user (ForeignKey): Пользователь, создавший отзыв.
        value (SmallIntegerField): Оценка продукта (от 1 до 5).
        text (TextField): Текст отзыва (опционально).
        image (ImageField): Изображение, прикрепленное к отзыву (опционально).
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Продукт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    value = models.SmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name='Оценка'
    )
    text = models.TextField(blank=True, verbose_name='Текст отзыва')
    likes = GenericRelation(
        Like,
        related_query_name='review',
        content_type_field='content_type',
        object_id_field='object_id'
    )
    image = models.ImageField(
        upload_to='images/reviews/%Y/%m/%d',
        blank=True,
        verbose_name='Изображение',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])]
    )

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created']
        indexes = [models.Index(fields=['product', '-created'])]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self) -> str:
        """Строковое представление отзыва.

        Returns:
            str: Название продукта, оценка и имя пользователя.
        """
        return f"{self.product.title}: {self.value} ({self.user.username})"

    def clean(self) -> None:
        """Валидация данных отзыва перед сохранением.

        Проверяет корректность оценки и уникальность отзыва для продукта и пользователя.

        Raises:
            ValidationError: Если оценка вне диапазона 1-5 или отзыв уже существует.
        """
        if self.value < 1 or self.value > 5:
            logger.warning(f"Invalid review value {self.value} for product {self.product.id}, user={self.user.id}")
            raise ValidationError("Оценка должна быть от 1 до 5.")
        if not self.pk and Review.objects.filter(product=self.product, user=self.user).exists():
            logger.warning(f"Review already exists for product {self.product.id}, user={self.user.id}")
            raise ValidationError("Вы уже оставили отзыв на этот продукт.")

    def save(self, *args, **kwargs) -> None:
        """Сохраняет отзыв с логированием.

        Логирует создание или обновление и выполняет валидацию.

        Raises:
            ValidationError: Если данные отзыва некорректны.
        """
        user_id = self.user.id if self.user else 'anonymous'
        if self.pk is None:
            logger.info(f"Creating review for product={self.product.id}, user={user_id}")
        else:
            logger.info(f"Updating review {self.pk}, user={user_id}")
        super().save(*args, **kwargs)

