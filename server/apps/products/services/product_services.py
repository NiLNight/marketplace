import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from typing import Dict, Any
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied  # Добавляем импорт

from apps.products.models import Product
from apps.products.exceptions import ProductServiceException, ProductNotFound

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
        safe_data = {k: v for k, v in data.items() if
                     k in ['title', 'price', 'category', 'stock', 'discount', 'description', 'thumbnail']}
        logger.info(f"Creating product with data={safe_data}, user={user_id}")
        try:
            product = Product(user=user, **data)
            product.full_clean()
            product.save()
            logger.info(f"Created product {product.id}, user={user_id}")
            return product
        except Exception as e:
            logger.error(f"Failed to create product: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка создания продукта: {str(e)}")

    @staticmethod
    @transaction.atomic
    def update_product(product_id: int, validated_data: Dict[str, Any], user: User) -> Product:
        """Обновляет существующий продукт.

        Args:
            product_id: Объект Product для обновления.
            validated_data: Проверенные данные для обновления.
            user: Пользователь, выполняющий обновление.

        Returns:
            Обновленный объект Product.

        Raises:
            ProductServiceException: Если данные некорректны или обновление не удалось.
            ProductNotFound: Если продукт не существует.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Updating product {product_id}, user={user_id}")
        try:
            instance = Product.objects.get(pk=product_id)
            # Проверяем права доступа
            if instance.user != user:
                raise PermissionDenied("У вас нет доступа к продукту.")  # Изменяем на PermissionDenied
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            logger.info(f"Updated product {product_id}, user={user_id}")
            return instance
        except Product.DoesNotExist:
            logger.warning(f"Product {product_id} not found")
            raise ProductNotFound(f"Продукт с ID {product_id} не найден")
        except ValidationError as e:
            logger.error(f"Failed to update product {product_id}: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка обновления продукта: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating product {product_id}: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Неожиданная ошибка при обновлении продукта: {str(e)}")

    @staticmethod
    @transaction.atomic
    def delete_product(product_id: int, user: User) -> None:
        """Выполняет мягкое удаление продукта (устанавливает is_active=False).

        Args:
            product_id: Объект Product для удаления.
            user: Пользователь, выполняющий удаление.

        Raises:
            ProductServiceException: Если удаление не удалось или пользователь не имеет прав.
            ProductNotFound: Если продукт не существует.
        """
        user_id = user.id if user else 'anonymous'
        logger.info(f"Deleting product {product_id}, user={user_id}")
        try:
            instance = Product.objects.get(pk=product_id)
            # Проверяем права доступа
            if instance.user != user:
                raise PermissionDenied("У вас нет доступа к продукту.")  # Изменяем на PermissionDenied
            instance.delete()
            logger.info(f"Deleted product {product_id}, user={user_id}")
        except Product.DoesNotExist:
            logger.warning(f"Product {product_id} not found")
            raise ProductNotFound(f"Продукт с ID {product_id} не найден")
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {str(e)}, user={user_id}")
            raise ProductServiceException(f"Ошибка удаления продукта: {str(e)}")
