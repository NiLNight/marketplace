# Generated by Django 5.1.5 on 2025-02-18 20:05

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
            name='EmailVerified',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confirmation_code', models.CharField(blank=True, max_length=6, null=True)),
                ('code_created_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_verified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Проверка почты',
                'verbose_name_plural': 'Проверка почты',
                'ordering': ['code_created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.CharField(max_length=255)),
                ('phone', models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator('^\\+\\d{9}$|^\\+\\d \\(\\d{3}\\) \\d{3}-\\d{2}-\\d{2}$', message="Номер телефона должен соответствовать шаблону: '+999999999' или +'9 (999) 999-99-99'.")])),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('avatar', models.ImageField(blank=True, default='images/avatars/default.png', upload_to='images/avatars/%Y/%m/%d', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])], verbose_name='Аватар')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Профиль',
                'verbose_name_plural': 'Профили',
                'ordering': ['user__id'],
                'indexes': [models.Index(fields=['public_id', 'id'], name='users_userp_public__ca76cd_idx')],
            },
        ),
    ]
