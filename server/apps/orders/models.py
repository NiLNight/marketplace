from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel

User = get_user_model()


class Delivery(models.Model):
    user = models.ForeignKey(User, related_name='deliveries', on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_primary = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'

    def __str__(self):
        return f"Delivery address for {User.username}"


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
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery = models.ForeignKey(Delivery, related_name='orders', on_delete=models.SET_NULL, null=True)

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
        return f"Order #{self.id} - {User.username}"
