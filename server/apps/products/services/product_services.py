from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers
from apps.products.models import Product


class ProductServices:
    @staticmethod
    def create_product(data):
        try:
            with transaction.atomic():
                product = Product.objects.create(**data)
                product.full_clean()
                return product
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

    @staticmethod
    def update_product(instance, validated_data):
        try:
            category_data = validated_data.pop('category_id', None)
            if category_data:
                instance.category = category_data
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.full_clean()
            instance.save()
            return instance
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

    @staticmethod
    def delete_product(product, user):
        if not (user.is_staff or product.user == user):
            raise serializers.ValidationError("Нет прав на удаление товара")
        product.is_active = False
        product.save()
