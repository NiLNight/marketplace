from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from typing import Dict, Any
from django.core.cache import cache


class BaseService:
    @staticmethod
    def create_instance(model_class, data: Dict[str, Any], user, cache_key_prefix: str, **extra_fields):
        try:
            with transaction.atomic():
                instance_data = {k: v for k, v in data.items() if k not in extra_fields}
                instance = model_class(user=user, **instance_data, **extra_fields)
                instance.full_clean()
                instance.save()
                cache.delete(f'{cache_key_prefix}_{instance.pk}')
                return instance
        except Exception as e:
            raise ValidationError(f"Ошибка создания: {str(e)}")

    @staticmethod
    def update_instance(instance, data: Dict[str, Any], user, allowed_fields: set, cache_key_prefix: str):
        if instance.user != user:
            raise PermissionDenied("Вы не автор.")
        data_to_update = {key: value for key, value in data.items() if key in allowed_fields}
        try:
            with transaction.atomic():
                for field, value in data_to_update.items():
                    setattr(instance, field, value)
                instance.full_clean()
                instance.save()
                cache.delete(f'{cache_key_prefix}_{instance.pk}')
                return instance
        except Exception as e:
            raise ValidationError(f"Ошибка обновления: {str(e)}")
