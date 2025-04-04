# Generated by Django 5.1.5 on 2025-03-12 13:54

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0004_delete_orderitem'),
        ('products', '0010_remove_product_unique_product_category'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='orders.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='products.product')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Предмет заказа/корзины',
                'verbose_name_plural': 'Предметы заказа/корзины',
                'indexes': [models.Index(fields=['user', 'product'], name='carts_order_user_id_fb6e63_idx'), models.Index(fields=['order', 'product'], name='carts_order_order_i_8cc303_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('order__isnull', True)), fields=('user', 'product'), name='unique_cart_product'), models.UniqueConstraint(condition=models.Q(('order__isnull', False)), fields=('order', 'product'), name='unique_order_product')],
            },
        ),
    ]
