# Generated by Django 5.1.5 on 2025-02-14 14:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created'], 'verbose_name': 'Товар', 'verbose_name_plural': 'Товары'},
        ),
    ]
