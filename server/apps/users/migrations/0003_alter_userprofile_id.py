# Generated by Django 5.1.5 on 2025-02-03 14:49

import shortuuid.django_fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_userprofile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='id',
            field=shortuuid.django_fields.ShortUUIDField(alphabet=None, length=22, max_length=22, prefix='', primary_key=True, serialize=False),
        ),
    ]
