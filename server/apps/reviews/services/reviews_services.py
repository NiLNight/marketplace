import logging
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Count, Prefetch, Q
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from typing import Dict, Any, Optional
from apps.reviews.models import Review
from apps.reviews.exceptions import ReviewNotFound, InvalidReviewData
from apps.products.models import Product
from apps.core.models import Like

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewService:
    """Сервис для управления отзывами пользователей о продуктах.

    Обрабатывает создание, получение, обновление и удаление отзывов с кэшированием и проверкой прав.
    """
    ALLOWED_ORDERING_FIELDS = ['created', '-created', 'likes', '-likes']

    @staticmethod
    def _validate_review_data(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Проверяет корректность данных для создания или обновления отзыва.

        Args:
            data (Dict[str, Any]): Данные для отзыва (продукт, оценка, текст, изображение).
            user_id (str): ID пользователя или 'anonymous'.

        Returns:
            Dict[str, Any]: Проверенные данные с объектом Product.

        Raises:
            InvalidReviewData: Если данные некорректны (неверный продукт, оценка, текст или изображение).
        """
        product = data.get('product')
        if isinstance(product, int):
            try:
                product = Product.objects.get(pk=product, is_active=True)
            except Product.DoesNotExist:
                logger.warning(f"Product {product} not found or inactive, user={user_id}")
                raise InvalidReviewData("Указанный продукт не существует или неактивен.")
        elif not isinstance(product, Product):
            logger.warning(f"Invalid product type {type(product)}, user={user_id}")
            raise InvalidReviewData("Поле product должно быть ID или объектом Product.")

        value = data.get('value')
        if not isinstance(value, int) or value < 1 or value > 5:
            logger.warning(f"Invalid review value {value}, user={user_id}")
            raise InvalidReviewData("Оценка должна быть целым числом от 1 до 5.")

        text = data.get('text', '')
        if text and len(text.strip()) > 1000:
            logger.warning(f"Review text too long, user={user_id}")
            raise InvalidReviewData("Текст отзыва не должен превышать 1000 символов.")

        image = data.get('image')
        if image:
            # Проверка размера изображения (максимум 5 МБ)
            max_size = 5 * 1024 * 1024  # 5 MB
            if hasattr(image, 'size') and image.size > max_size:
                logger.warning(f"Image size {image.size} exceeds limit {max_size}, user={user_id}")
                raise InvalidReviewData("Изображение не должно превышать 5 МБ.")

            # Проверка формата изображения
            allowed_formats = ['image/jpeg', 'image/png']
            if hasattr(image, 'content_type') and image.content_type not in allowed_formats:
                logger.warning(f"Invalid image format {image.content_type}, user={user_id}")
                raise InvalidReviewData("Изображение должно быть в формате JPEG или PNG.")

        return {
            'product': product,
            'value': value,
            'text': text.strip() if text else '',
            'image': image
        }

    @staticmethod
    def get_reviews(product_id: int) -> QuerySet:
        """Получает список отзывов для указанного продукта.

        Args:
            product_id (int): ID продукта, для которого нужно получить отзывы.

        Returns:
            QuerySet: Список отзывов с предзагруженными данными о продукте, пользователе и лайках.

        Raises:
            ReviewNotFound: Если продукт не существует или отзывы не найдены.
        """
        logger.info(f"Retrieving reviews for product={product_id}, user=anonymous")
        try:
            if not Product.objects.filter(pk=product_id, is_active=True).exists():
                logger.warning(f"Product {product_id} not found or inactive")
                raise ReviewNotFound("Указанный продукт не существует или неактивен.")

            content_type = ContentType.objects.get_for_model(Review)
            reviews = Review.objects.filter(
                product_id=product_id
            ).select_related('product', 'user').prefetch_related(
                Prefetch(
                    'likes',
                    queryset=Like.objects.filter(content_type=content_type),
                    to_attr='review_likes'
                )
            )
            logger.info(f"Retrieved {reviews.count()} reviews for product={product_id}")
            return reviews
        except Exception as e:
            logger.error(f"Error retrieving reviews for product={product_id}: {str(e)}")
            raise ReviewNotFound(f"Ошибка получения отзывов: {str(e)}")

    @staticmethod
    def apply_ordering(reviews: QuerySet, ordering: Optional[str]) -> QuerySet:
        """Применяет сортировку к списку отзывов.

        Args:
            reviews (QuerySet): Список отзывов для сортировки.
            ordering (str): Поле для сортировки (например, 'created', '-likes').

        Returns:
            QuerySet: Отсортированный список отзывов.

        Raises:
            InvalidReviewData: Если поле сортировки недопустимо.
        """
        if not ordering:
            return reviews
        if ordering.lstrip('-') not in ReviewService.ALLOWED_ORDERING_FIELDS:
            logger.warning(f"Invalid ordering field {ordering}")
            raise InvalidReviewData(f"Недопустимое поле сортировки: {ordering}")

        if ordering.lstrip('-') == 'likes':
            # Сортировка по количеству лайков
            content_type = ContentType.objects.get_for_model(Review)
            ordering_field = 'likes_count' if ordering == 'likes' else '-likes_count'
            reviews = reviews.annotate(
                likes_count=Count('likes', filter=Q(likes__content_type=content_type))
            ).order_by(ordering_field)
        else:
            reviews = reviews.order_by(ordering)
        return reviews

    @staticmethod
    @transaction.atomic
    def create_review(data: Dict[str, Any], user: User) -> Review:
        """Создает новый отзыв о продукте.

        Args:
            data (Dict[str, Any]): Данные для создания отзыва (продукт, оценка, текст, изображение).
            user (User): Пользователь, создающий отзыв.

        Returns:
            Review: Созданный объект отзыва.

        Raises:
            InvalidReviewData: Если данные некорректны или пользователь уже оставил отзыв.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Creating review for product={data.get('product')}, user={user_id}")

        try:
            validated_data = ReviewService._validate_review_data(data, user_id)
            review = Review(
                user=user,
                product=validated_data['product'],
                value=validated_data['value'],
                text=validated_data['text'],
                image=validated_data.get('image')
            )
            review.full_clean()
            review.save()
            logger.info(f"Created Review {review.id}, user={user_id}")
            return review
        except Exception as e:
            logger.error(f"Failed to create Review: {str(e)}, data={data}, user={user_id}")
            raise InvalidReviewData(f"Ошибка создания отзыва: {str(e)}")

    @staticmethod
    @transaction.atomic
    def update_review(review_id: int, data: Dict[str, Any], user: User) -> Review:
        """Обновляет существующий отзыв.

        Args:
            review_id (int): ID отзыва для обновления.
            data (Dict[str, Any]): Данные для обновления (оценка, текст, изображение).
            user (User): Пользователь, пытающийся обновить отзыв.

        Returns:
            Review: Обновленный объект отзыва.

        Raises:
            ReviewNotFound: Если отзыв не существует.
            PermissionDenied: Если пользователь не является автором отзыва.
            InvalidReviewData: Если данные некорректны.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Updating review {review_id}, user={user_id}")

        try:
            review = Review.objects.get(pk=review_id)
            if review.user != user:
                logger.warning(f"Permission denied for Review {review_id}, user={user_id}")
                raise PermissionDenied("Только автор может обновить отзыв.")

            validated_data = ReviewService._validate_review_data(data, user_id)
            allowed_fields = {'value', 'text', 'image'}
            for field, value in validated_data.items():
                if field in allowed_fields:
                    setattr(review, field, value)

            review.full_clean()
            review.save()
            logger.info(f"Updated Review {review_id}, user={user_id}")
            return review
        except Review.DoesNotExist:
            logger.warning(f"Review {review_id} not found, user={user_id}")
            raise ReviewNotFound()
        except Exception as e:
            logger.error(f"Failed to update Review {review_id}: {str(e)}, data={data}, user={user_id}")
            raise InvalidReviewData(f"Ошибка обновления отзыва: {str(e)}")