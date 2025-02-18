from django.core.validators import MinValueValidator
from django.db import models
from apps.users.models import User
from apps.products.models import Product
from apps.core.models import TimeStampedModel


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

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['order', 'product'], name='unique_order_product')
        ]
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


class Delivery(models.Model):
    user = models.ForeignKey(User, related_name='deliveries', on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Delivery addresses'
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]

    def __str__(self):
        return f"Delivery address for {self.user.username}"