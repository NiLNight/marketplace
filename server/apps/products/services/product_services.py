from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.products.models import Product


class ProductServices:
    @staticmethod
    def create_product(user, **data):
        """Создание товара с валидацией"""
        with transaction.atomic():
            product = Product.objects.create(user=user, **data)
            product.full_clean()
            return product

    @staticmethod
    def update_product(product, user, **data):
        """Обновление товара с проверкой прав"""
        if not (user.is_staff or product.user == user):
            raise PermissionDenied("Нет прав на изменение товара")

        for key, value in data.items():
            setattr(product, key, value)
        product.full_clean()
        product.save()
        return product

    @staticmethod
    def delete_product(product, user):
        """Мягкое удаление товара"""
        if not (user.is_staff or product.user == user):
            raise PermissionDenied("Нет прав на удаление товара")
        product.is_active = False
        product.save()
