from django.db import models


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
