from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from apps.core.models import TimeStampedModel
from apps.products.models import Product
from django.core.validators import MinValueValidator

User = get_user_model()


class OrderQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status='pending')

    def completed(self):
        return self.filter(status='delivered')


class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created']),
        ]
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items', null=True, blank=True)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            # Уникальность товара в корзине для пользователя (order is null)
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=Q(order__isnull=True),
                name='unique_cart_product'
            ),
            # Уникальность товара в заказе (order is not null)
            models.UniqueConstraint(
                fields=['order', 'product'],
                condition=Q(order__isnull=False),
                name='unique_order_product'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'product']),
            models.Index(fields=['order', 'product']),
        ]
        verbose_name = "Предмет заказа/корзины"
        verbose_name_plural = "Предметы заказа/корзины"

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def clean(self):
        """Валидация: элемент не может быть одновременно в корзине и в заказе."""
        if self.user and self.order:
            raise ValidationError("Элемент не может одновременно принадлежать пользователю (корзина) и заказу.")
        if not self.user and not self.order:
            raise ValidationError("Элемент должен быть привязан либо к пользователю, либо к заказу.")


class Delivery(models.Model):
    user = models.ForeignKey(User, related_name='deliveries', on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'

    def __str__(self):
        return f"Delivery address for {User.username}"
