from django.db import models
from django.contrib.auth import get_user_model

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
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=models.Q(order__isnull=True),
                name='unique_user_product_cart'
            ),
            models.UniqueConstraint(
                fields=['session_key', 'product'],
                condition=models.Q(order__isnull=True),
                name='unique_session_product_cart'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'order']),
            models.Index(fields=['session_key', 'order']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

    def update_price(self):
        """Обновляет цену, если товар еще не в заказе"""
        if not self.order:
            new_price = self.product.price * (100 - self.product.discount) / 100
            if self.price != new_price:
                self.price = new_price
                self.save(update_fields=['price', 'price_updated'])


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
