import logging
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.utils import unique_slugify

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerified(models.Model):
    """Модель для хранения данных о верификации электронной почты пользователя.

    Хранит информацию о коде подтверждения и времени его создания для пользователя.

    Attributes:
        user: Связь с пользователем (один-к-одному).
        confirmation_code: Код подтверждения (6 символов).
        code_created_at: Время создания кода подтверждения.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_verified',
        verbose_name='Пользователь'
    )
    confirmation_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name='Код подтверждения'
    )
    code_created_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время создания кода'
    )

    class Meta:
        """Метаданные модели EmailVerified."""
        ordering = ['code_created_at']
        verbose_name = 'Проверка почты'
        verbose_name_plural = 'Проверка почты'
        indexes = [
            models.Index(fields=['code_created_at']),
        ]

    def __str__(self) -> str:
        """Возвращает строковое представление объекта верификации почты.

        Returns:
            Строка в формате 'email-время_создания_кода'.
        """
        return f'{self.user.email}-{self.code_created_at}'


class UserProfile(models.Model):
    """Модель профиля пользователя.

    Хранит дополнительную информацию о пользователе, включая публичный идентификатор,
    номер телефона, дату рождения и аватар.

    Attributes:
        public_id: Уникальный публичный идентификатор профиля.
        user: Связь с пользователем (один-к-одному).
        phone: Номер телефона с валидацией формата.
        birth_date: Дата рождения пользователя.
        avatar: Изображение аватара пользователя.
    """
    public_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Публичный идентификатор'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[RegexValidator(
            r'^\+\d{9}$|^\+\d \(\d{3}\) \d{3}-\d{2}-\d{2}$',
            message="Номер телефона должен соответствовать шаблону: '+999999999' или '+9 (999) 999-99-99'."
        )],
        verbose_name='Номер телефона'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )
    avatar = models.ImageField(
        upload_to='images/avatars/%Y/%m/%d',
        default='images/avatars/default.png',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])],
        verbose_name='Аватар'
    )

    class Meta:
        """Метаданные модели UserProfile."""
        ordering = ['user__id']
        indexes = [
            models.Index(fields=['public_id']),
        ]
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def save(self, *args, **kwargs) -> None:
        """Сохраняет профиль пользователя с генерацией публичного идентификатора и логированием.

        Если `public_id` не задан, генерируется уникальный идентификатор на основе имени пользователя.

        Raises:
            Exception: Если сохранение профиля не удалось.
        """
        user_id = self.user.id if self.user else 'anonymous'
        action = 'Creating' if self.pk is None else 'Updating'
        logger.info(f"{action} user profile for user={user_id}, data={self.__dict__}")
        try:
            if not self.public_id:
                self.public_id = unique_slugify(self.user.username)
            super().save(*args, **kwargs)
            logger.info(f"Successfully {action.lower()} user profile {self.pk}, user={user_id}")
        except Exception as e:
            logger.error(f"Failed to {action.lower()} user profile: {str(e)}, user={user_id}")
            raise

    def __str__(self) -> str:
        """Возвращает строковое представление профиля пользователя.

        Returns:
            Строка в формате 'Профиль <имя_пользователя>'.
        """
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при создании нового пользователя.

    Args:
        sender: Модель, отправившая сигнал (User).
        instance: Экземпляр пользователя.
        created: Флаг, указывающий, был ли пользователь создан.
        **kwargs: Дополнительные аргументы.
    """
    if created:
        logger.info(f"Creating user profile for new user={instance.id}")
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при обновлении данных пользователя.

    Args:
        sender: Модель, отправившая сигнал (User).
        instance: Экземпляр пользователя.
        **kwargs: Дополнительные аргументы.
    """
    logger.info(f"Saving user profile for user={instance.id}")
    instance.profile.save()
