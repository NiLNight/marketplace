# Generated by Django 5.1.5 on 2025-03-02 16:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_alter_category_options_alter_category_description_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created'], 'verbose_name': 'Товар', 'verbose_name_plural': 'Товары'},
        ),
    ]
