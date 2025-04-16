from django.contrib.auth import get_user_model
from apps.reviews.services.base_service import BaseService
from typing import Dict, Any
from apps.reviews.models import Comment

User = get_user_model()


class CommentService(BaseService):
    @staticmethod
    def create_comment(data: Dict[str, Any], user: User) -> Comment:
        """Создание нового комментария."""
        return BaseService.create_instance(
            Comment, data, user, 'comments', review=data['review'],
            parent=data.get('parent')
        )

    @staticmethod
    def update_comment(comment: Comment, data: Dict[str, Any], user: User) -> Comment:
        """Обновление комментария"""
        return BaseService.update_instance(
            comment, data, user, {'text'}, 'comments'
        )
