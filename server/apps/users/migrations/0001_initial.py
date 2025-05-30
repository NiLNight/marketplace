# Generated by Django 5.1.5 on 2025-05-30 12:47

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailVerified",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "confirmation_code",
                    models.CharField(
                        blank=True,
                        max_length=6,
                        null=True,
                        verbose_name="Код подтверждения",
                    ),
                ),
                (
                    "code_created_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Время создания кода"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_verified",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Проверка почты",
                "verbose_name_plural": "Проверка почты",
                "ordering": ["code_created_at"],
                "indexes": [
                    models.Index(
                        fields=["code_created_at"],
                        name="users_email_code_cr_b296f4_idx",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Публичный идентификатор",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\+\\d{9}$|^\\+\\d \\(\\d{3}\\) \\d{3}-\\d{2}-\\d{2}$",
                                message="Номер телефона должен соответствовать шаблону: '+999999999' или '+9 (999) 999-99-99'.",
                            )
                        ],
                        verbose_name="Номер телефона",
                    ),
                ),
                (
                    "birth_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Дата рождения"
                    ),
                ),
                (
                    "avatar",
                    models.ImageField(
                        blank=True,
                        default="images/avatars/default.png",
                        upload_to="images/avatars/%Y/%m/%d",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]
                            )
                        ],
                        verbose_name="Аватар",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Профиль",
                "verbose_name_plural": "Профили",
                "ordering": ["user__id"],
                "indexes": [
                    models.Index(
                        fields=["public_id"], name="users_userp_public__afe67f_idx"
                    )
                ],
            },
        ),
    ]
