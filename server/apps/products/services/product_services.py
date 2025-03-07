# product_services.py
from django.db import transaction
from apps.products.models import Product
from apps.products.exceptions import ProductServiceException


class ProductServices:

    @staticmethod
    def create_product(data):
        try:
            with transaction.atomic():
                product = Product(**data)
                product.full_clean()
                product.save()
                return product
        except Exception as e:
            raise ProductServiceException(f"Ошибка создания продукта: {str(e)}")

    @staticmethod
    def update_product(instance, validated_data):
        try:
            with transaction.atomic():
                for field, value in validated_data.items():
                    setattr(instance, field, value)
                instance.full_clean()
                instance.save()
                return instance
        except Exception as e:
            raise ProductServiceException(f"Ошибка обновления продукта: {str(e)}")

    @staticmethod
    def delete_product(instance):
        try:
            with transaction.atomic():
                instance.is_active = False
                instance.save(update_fields=['is_active'])
        except Exception as e:
            raise ProductServiceException(f"Ошибка удаления продукта: {str(e)}")
