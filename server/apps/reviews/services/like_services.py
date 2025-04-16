from typing import Dict

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from django.core.cache import cache

User = get_user_model()


class LikeService:
    @staticmethod
    def toggle_like(model_class, instance, user: User, cache_key_prefix: str) -> Dict[str, str]:
        """Переключает лайк для обзоров и комментариев."""
        try:
            like, created = model_class.objects.get_or_create(
                **{model_class.__name__.lower().replace('like', ''): instance, 'user': user})
            if not created:
                like.delete()
                action = 'unliked'
            else:
                action = 'liked'
            cache.delete(f'{cache_key_prefix}_{instance.pk}')
            return {'action': action}
        except IntegrityError:
            raise ValidationError("Ошибка при обработке лайка.")
