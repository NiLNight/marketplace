import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.products.models import Product
from apps.products.exceptions import ProductServiceException, ProductNotFound
from typing import Dict, Any

User = get_user_model()
logger = logging.getLogger(__name__)


class ProductServices:
    """Сервис для управления продуктами.

    Предоставляет методы для создания, обновления и удаления продуктов с валидацией и логированием.
    """

    @staticmethod
    @transaction.atomic
    def create_product(data: Dict[str, Any], user: User) -> Product:
        """Создает новый продукт.

        Args:
            data: Данные для создания продукта (название, цена, категория и т.д.).
            user: Пользователь, создающий продукт.

        Returns:
            Созданный объект Product.

        Raises:
            ProductServiceException: Если данные некорректны или создание не удалось.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Creating product with data={data}, user={user_id}")
        try:
            product = Product(user=user, **data)
            product.full_clean()
            product.save()
            logger.info(f"Successfully created product {product.id}, user={user_id}")
            return product
        except Exception as e:
            logger.error(f"Failed to create product: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка создания продукта: {str(e)}")

    @staticmethod
    @transaction.atomic
    def update_product(instance: Product, validated_data: Dict[str, Any], user: User) -> Product:
        """Обновляет существующий продукт.

        Args:
            instance: Объект Product для обновления.
            validated_data: Проверенные данные для обновления.
            user: Пользователь, выполняющий обновление.

        Returns:
            Обновленный объект Product.

        Raises:
            ProductServiceException: Если данные некорректны или обновление не удалось.
            ProductNotFound: Если продукт не существует.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Updating product {instance.id}, user={user_id}")
        try:
            if instance.user != user and not user.is_staff:
                logger.warning(f"Permission denied for product {instance.id}, user={user_id}")
                raise ProductServiceException("Только владелец или администратор может обновить продукт.")

            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            logger.info(f"Successfully updated product {instance.id}, user={user_id}")
            return instance
        except Exception as e:
            logger.error(f"Failed to update product {instance.id}: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка обновления продукта: {str(e)}")

    @staticmethod
    @transaction.atomic
    def delete_product(instance: Product, user: User) -> None:
        """Выполняет мягкое удаление продукта (устанавливает is_active=False).

        Args:
            instance: Объект Product для удаления.
            user: Пользователь, выполняющий удаление.

        Raises:
            ProductServiceException: Если удаление не удалось или пользователь не имеет прав.
            ProductNotFound: Если продукт не существует.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Deleting product {instance.id}, user={user_id}")
        try:
            if instance.user != user and not user.is_staff:
                logger.warning(f"Permission denied for product {instance.id}, user={user_id}")
                raise ProductServiceException("Только владелец или администратор может удалить продукт.")

            instance.is_active = False
            instance.save(update_fields=['is_active'])
            logger.info(f"Successfully deleted product {instance.id}, user={user_id}")
        except Exception as e:
            logger.error(f"Failed to delete product {instance.id}: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка удаления продукта: {str(e)}")
