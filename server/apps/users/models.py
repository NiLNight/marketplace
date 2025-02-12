from django.contrib.auth.models import User
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.services.utils import unique_slugify


class EmailVerified(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verified')
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)
    code_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['code_created_at']
        verbose_name = 'Проверка почты'
        verbose_name_plural = 'Проверка почты'

    def __str__(self):
        return f'{self.user.email}-{self.code_created_at}'


class UserProfile(models.Model):
    public_id = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[RegexValidator(
            r'^\+\d{9}$|^\+\d \(\d{3}\) \d{3}-\d{2}-\d{2}$',
            message="Номер телефона должен соответствовать шаблону: '+999999999' или +'9 (999) 999-99-99'.")]
    )
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='images/avatars/%Y/%m/%d',
        default='images/avatars/default.png',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])])

    class Meta:
        ordering = ['user__id']
        indexes = [models.Index(fields=['public_id', 'id'])]
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = unique_slugify(self.user.username)
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
