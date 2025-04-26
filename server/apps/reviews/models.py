import logging
from django.contrib.auth.models import User
from django.db import models
from apps.core.models import TimeStampedModel
from apps.products.models import Product
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Review(TimeStampedModel):
    """Модель отзыва о продукте.

    Хранит информацию о продукте, пользователе, оценке и тексте отзыва.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='Продукт')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name='Пользователь')
    value = models.SmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name='Оценка')
    text = models.TextField(blank=True, verbose_name='Текст отзыва')
    image = models.ImageField(upload_to='images/reviews/%Y/%m/%d', blank=True, verbose_name='Изображение')

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

        Raises:
            ValidationError: Если оценка вне диапазона 1-5.
        """
        if self.value < 1 or self.value > 5:
            logger.warning(f"Invalid review value {self.value} for product {self.product.id}, user={self.user.id}")
            raise ValidationError("Оценка должна быть от 1 до 5.")

    def save(self, *args, **kwargs) -> None:
        """Сохраняет отзыв с логированием.

        Raises:
            ValidationError: Если валидация не пройдена.
        """
        user_id = self.user.id if self.user else 'anonymous'
        if self.pk is None:
            logger.info(f"Creating review for product={self.product.id}, user={user_id}")
        else:
            logger.info(f"Updating review {self.pk}, user={user_id}")
        super().save(*args, **kwargs)


class ReviewLike(models.Model):
    """Модель лайка для отзыва."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')
        verbose_name = 'Лайк отзыва'
        verbose_name_plural = 'Лайки отзывов'
