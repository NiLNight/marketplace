from django.core.exceptions import PermissionDenied
from django.db import transaction
from apps.products.models import Product


class ProductServices:
    @staticmethod
    def create_product(data):
        """Создание товара с валидацией"""
        with transaction.atomic():
            product = Product.objects.create(**data, search_vector='test')
            product.full_clean()
            return product

    @staticmethod
    def update_product(instance, validated_data):
        category_data = validated_data.pop('category_id', None)
        if category_data:
            instance.category = category_data

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.full_clean()
        instance.save()
        return instance

    @staticmethod
    def delete_product(product, user):
        """Мягкое удаление товара"""
        if not (user.is_staff or product.user == user):
            raise PermissionDenied("Нет прав на удаление товара")
        product.is_active = False
        product.save()
