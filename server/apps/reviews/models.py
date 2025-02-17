from django.contrib.auth.models import User
from django.db import models

from apps.products.models import Product


class Rating(models.Model):
    """
    Модель рейтинга: От 1 до 5
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings', verbose_name='Запись')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь')
    value = models.BigIntegerField(default=True, verbose_name='Значение')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    ip_address = models.GenericIPAddressField(verbose_name='IP Адрес')

    class Meta:
        unique_together = ('product', 'ip_address')
        ordering = ['-time_create']
        indexes = [models.Index(fields=['-time_create', 'value'])]
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'

    def __str__(self):
        return self.product.title
