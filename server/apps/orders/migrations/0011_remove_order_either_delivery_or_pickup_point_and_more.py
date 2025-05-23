# Generated by Django 5.1.5 on 2025-05-21 15:36

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0005_pickuppoint_district_delete_delivery'),
        ('orders', '0010_remove_order_delivery'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='order',
            name='either_delivery_or_pickup_point',
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(condition=models.Q(('pickup_point__isnull', True), _negated=True), name='either_pickup_point'),
        ),
    ]
