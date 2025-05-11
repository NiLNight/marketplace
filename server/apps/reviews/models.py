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

    Хранит информацию о продукте, авторе, оценке, тексте и изображении отзыва.

    Attributes:
        product: Ссылка на продукт, к которому относится отзыв.
        user: Пользователь, оставивший отзыв.
        value: Оценка продукта (от 1 до 5).
        text: Текст отзыва (опционально).
        image: Изображение, прикрепленное к отзыву (опционально).
        likes: Связь с моделью лайков.
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
    text = models.TextField(
        blank=True,
        verbose_name='Текст отзыва'
    )
    image = models.ImageField(
        upload_to='images/reviews/%Y/%m/%d',
        blank=True,
        verbose_name='Изображение',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    likes = GenericRelation(
        Like,
        related_query_name='review',
        content_type_field='content_type',
        object_id_field='object_id'
    )

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created']
        indexes = [models.Index(fields=['product', '-created'])]
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self) -> str:
        """Возвращает строковое представление отзыва.

        Returns:
            Название продукта, оценка и имя пользователя.
        """
        return f"{self.product.title}: {self.value} ({self.user.username})"

    def clean(self) -> None:
        """Проверяет данные отзыва перед сохранением.

        Raises:
            ValidationError: Если оценка некорректна или отзыв уже существует.
        """
        if self.value < 1 or self.value > 5:
            logger.warning(f"Invalid review value {self.value}, product={self.product.id}, user={self.user.id}")
            raise ValidationError("Оценка должна быть от 1 до 5.")
        if not self.pk and Review.objects.filter(product=self.product, user=self.user).exists():
            logger.warning(f"Review already exists for product={self.product.id}, user={self.user.id}")
            raise ValidationError("Вы уже оставили отзыв на этот продукт.")

    def save(self, *args, **kwargs) -> None:
        """Сохраняет отзыв с логированием.

        Raises:
            ValidationError: Если данные отзыва некорректны.
        """
        user_id = self.user.id if self.user else 'anonymous'
        action = 'Creating' if self.pk is None else 'Updating'
        logger.info(f"{action} review for product={self.product.id}, user={user_id}")
        try:
            if self.pk:
                old_review = Review.objects.get(pk=self.pk)
                if old_review.image and self.image != old_review.image:
                    old_review.image.delete(save=False)
            super().save(*args, **kwargs)
            logger.info(f"Successfully {action.lower()} review {self.pk}, user={user_id}")
        except Exception as e:
            logger.error(f"Failed to {action.lower()} review: {str(e)}, user={user_id}")
            raise
