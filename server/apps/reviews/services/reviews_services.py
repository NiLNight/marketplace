import logging
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Count, Prefetch, Q
from django.db import transaction, IntegrityError
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

    Предоставляет методы для создания, получения, обновления и удаления отзывов с учетом прав доступа,
    кэширования и валидации данных.
    """
    ALLOWED_ORDERING_FIELDS = ['created', '-created', 'likes', '-likes', 'value', '-value']

    @staticmethod
    def _validate_review_data(data: Dict[str, Any], user_id: str, review: Optional[Review] = None) -> Dict[str, Any]:
        """Валидирует данные для создания или обновления отзыва.

        Args:
            data: Данные отзыва, включая оценку, текст и изображение (продукт опционален при обновлении).
            user_id: Идентификатор пользователя или 'anonymous'.
            review: Существующий отзыв для обновления (опционально, используется для получения продукта).

        Returns:
            Проверенные данные с объектом Product.

        Raises:
            InvalidReviewData: Если данные некорректны (продукт, оценка, текст, изображение).
        """
        product = data.get('product')
        if review:
            # Для обновления используем продукт из существующего отзыва
            product = review.product
        elif isinstance(product, int):
            try:
                product = Product.objects.get(pk=product, is_active=True)
            except Product.DoesNotExist:
                logger.warning(f"Product {product} not found or inactive, user={user_id}")
                raise InvalidReviewData("Продукт не существует или неактивен.")
        elif not isinstance(product, Product):
            logger.warning(f"Invalid product type {type(product)}, user={user_id}")
            raise InvalidReviewData("Поле product должно быть ID или объектом Product.")

        value = data.get('value')
        if value is not None and (not isinstance(value, int) or value < 1 or value > 5):
            logger.warning(f"Invalid review value {value}, user={user_id}")
            raise InvalidReviewData("Оценка должна быть числом от 1 до 5.")

        text = data.get('text', '')
        if text and len(text.strip()) > 1000:
            logger.warning(f"Review text exceeds 1000 characters, user={user_id}")
            raise InvalidReviewData("Текст отзыва не должен превышать 1000 символов.")

        image = data.get('image')
        if image:
            max_size = 5 * 1024 * 1024  # 5 MB
            if hasattr(image, 'size') and image.size > max_size:
                logger.warning(f"Image size {image.size} exceeds limit {max_size}, user={user_id}")
                raise InvalidReviewData("Изображение не должно превышать 5 МБ.")

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
        """Получает отзывы для указанного продукта.

        Args:
            product_id: Идентификатор продукта.

        Returns:
            QuerySet с отзывами, предзагруженными данными о продукте, пользователе и лайках.

        Raises:
            ReviewNotFound: Если продукт не существует или отзывы не найдены.
        """
        logger.info(f"Fetching reviews for product={product_id}")
        try:
            if not Product.objects.filter(pk=product_id, is_active=True).exists():
                logger.warning(f"Product {product_id} not found or inactive")
                raise ReviewNotFound("Продукт не существует или неактивен.")

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
            logger.info(f"Found {reviews.count()} reviews for product={product_id}")
            return reviews
        except Exception as e:
            logger.error(f"Failed to fetch reviews for product={product_id}: {str(e)}")
            raise ReviewNotFound(f"Ошибка при получении отзывов: {str(e)}")

    @staticmethod
    def apply_ordering(reviews: QuerySet, ordering: Optional[str]) -> QuerySet:
        """Применяет сортировку к списку отзывов.

        Args:
            reviews: QuerySet с отзывами.
            ordering: Поле для сортировки (например, 'created', '-likes').

        Returns:
            Отсортированный QuerySet.

        Raises:
            InvalidReviewData: Если поле сортировки недопустимо.
        """
        if not ordering:
            return reviews
        if ordering.lstrip('-') not in ReviewService.ALLOWED_ORDERING_FIELDS:
            logger.warning(f"Invalid ordering field: {ordering}")
            raise InvalidReviewData(f"Недопустимое поле сортировки: {ordering}")

        if ordering.lstrip('-') == 'likes':
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
            data: Данные отзыва (продукт, оценка, текст, изображение).
            user: Пользователь, создающий отзыв.

        Returns:
            Созданный объект Review.

        Raises:
            InvalidReviewData: Если данные некорректны или пользователь уже оставил отзыв.
        """
        user_id = user.id
        logger.info(f"Creating review for product={data.get('product')}, user={user_id}")
        validated_data = ReviewService._validate_review_data(data, user_id)
        try:
            review = Review(
                user=user,
                product=validated_data['product'],
                value=validated_data['value'],
                text=validated_data['text'],
                image=validated_data.get('image')
            )
            review.full_clean()
            review.save()
            logger.info(f"Successfully created review {review.id}, user={user_id}")
            return review
        except IntegrityError:
            logger.warning(f"User {user_id} already reviewed product {validated_data['product'].id}")
            raise InvalidReviewData("Вы уже оставили отзыв на этот продукт.")
        except Exception as e:
            logger.error(f"Failed to create review: {str(e)}, user={user_id}")
            raise InvalidReviewData(f"Ошибка создания отзыва: {str(e)}")

    @staticmethod
    @transaction.atomic
    def update_review(review_id: int, data: Dict[str, Any], user: User) -> Review:
        """Обновляет существующий отзыв.

        Args:
            review_id: Идентификатор отзыва.
            data: Данные для обновления (оценка, текст, изображение).
            user: Аутентифицированный пользователь, обновляющий отзыв.

        Returns:
            Обновленный объект Review.

        Raises:
            ReviewNotFound: Если отзыв или продукт не существуют/неактивны.
            PermissionDenied: Если пользователь не является автором.
            InvalidReviewData: Если данные некорректны.
        """
        logger.info(f"Updating review {review_id}, user={user.id}")
        try:
            # Получаем отзыв с предзагрузкой продукта
            review = Review.objects.select_related('product').get(pk=review_id)

            # Проверяем, что продукт активен
            if not review.product.is_active:
                logger.warning(f"Product {review.product.id} is inactive, review={review_id}, user={user.id}")
                raise ReviewNotFound("Продукт неактивен.")

            # Проверяем права доступа
            if review.user != user:
                logger.warning(f"Permission denied for review {review_id}, user={user.id}")
                raise PermissionDenied("Только автор может обновить отзыв.")

            validated_data = ReviewService._validate_review_data(data, user.id, review=review)
            for field, value in validated_data.items():
                if field in {'value', 'text', 'image'} and value is not None:
                    setattr(review, field, value)

            review.full_clean()
            review.save()
            logger.info(f"Successfully updated review {review_id}, user={user.id}")
            return review

        except Review.DoesNotExist:
            logger.warning(f"Review {review_id} not found, user={user.id}")
            raise ReviewNotFound("Отзыв не найден.")
        except Exception as e:
            logger.error(f"Failed to update review {review_id}: {str(e)}, user={user.id}")
            raise InvalidReviewData(f"Ошибка обновления отзыва: {str(e)}")
