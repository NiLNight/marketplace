# Generated by Django 5.1.5 on 2025-05-09 13:36

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_product_popularity_score_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['title', 'category'], name='title_category_idx'),
        ),
    ]
