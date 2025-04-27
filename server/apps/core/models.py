import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class TimeStampedModel(models.Model):
    """Абстрактная модель для добавления временных меток к моделям.

    Предоставляет поля created и updated для отслеживания времени создания и
    последнего обновления записи.

    Attributes:
        created (DateTimeField): Дата и время создания записи, устанавливается автоматически.
        updated (DateTimeField): Дата и время последнего обновления записи, обновляется автоматически.
    """
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
        help_text='Время создания записи.'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
        help_text='Время последнего обновления записи.'
    )

    class Meta:
        """Метаданные модели TimeStampedModel.

        Указывает, что модель является абстрактной и не создает таблицу в базе данных.
        """
        abstract = True


class Like(TimeStampedModel):
    """Модель для лайков к различным сущностям.

    Использует ContentType для связи с любой моделью (например, Review, Comment).

    Атрибуты:
        user (ForeignKey): Пользователь, поставивший лайк.
        content_type (ForeignKey): Тип связанной сущности (например, Review или Comment).
        object_id (PositiveIntegerField): ID связанной сущности.
        content_object (GenericForeignKey): Обобщенная связь с сущностью.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Пользователь'
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Тип объекта'
    )
    object_id = models.PositiveIntegerField(verbose_name='ID объекта')
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'content_type', 'object_id'])
        ]
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'

    def __str__(self) -> str:
        """Строковое представление лайка.

        Returns:
            str: Описание лайка с указанием пользователя и объекта.
        """
        return f"Лайк от {self.user.username} для {self.content_type.model}:{self.object_id}"

    def clean(self) -> None:
        """Валидация данных лайка перед сохранением.

        Проверяет, что объект существует.

        Raises:
            ValidationError: Если связанный объект не существует.
        """
        try:
            self.content_type.get_object_for_this_type(pk=self.object_id)
        except self.content_type.model_class().DoesNotExist:
            logger.warning(f"Object {self.content_type.model}:{self.object_id} does not exist, user={self.user.id}")
            raise ValidationError(f"Объект {self.content_type.model} с ID {self.object_id} не существует.")
