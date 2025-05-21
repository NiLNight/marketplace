import logging
from django.db import transaction, DatabaseError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from typing import Dict, Any
from apps.delivery.models import Delivery
from apps.delivery.exceptions import DeliveryNotFound, DeliveryServiceException

User = get_user_model()
logger = logging.getLogger(__name__)


class DeliveryService:
    """Сервис для управления адресами доставки.

    Предоставляет методы для создания, обновления и удаления адресов доставки с валидацией и логированием.
    """

    @staticmethod
    @transaction.atomic
    def create_delivery(data: Dict[str, Any], user: User) -> Delivery:
        """Создает новый адрес доставки.

        Args:
            data: Данные для создания адреса (валидируются сериализатором).
            user: Пользователь, создающий адрес.

        Returns:
            Созданный объект Delivery.

        Raises:
            DeliveryServiceException: Если данные некорректны или создание не удалось.
        """
        user_id = user.id
        logger.info(f"Creating delivery with data={data}, user={user_id}")
        try:
            delivery = Delivery(user=user, **data)
            delivery.full_clean()
            delivery.save()
            logger.info(f"Created delivery {delivery.id}, user={user_id}")
            return delivery
        except ValidationError as e:
            logger.error(f"Validation failed for delivery: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка валидации адреса доставки: {str(e)}")
        except DatabaseError as e:
            logger.error(f"Database error while creating delivery: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка базы данных при создании адреса доставки: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while creating delivery: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Неизвестная ошибка при создании адреса доставки: {str(e)}")

    @staticmethod
    @transaction.atomic
    def update_delivery(instance: Delivery, validated_data: Dict[str, Any], user: User) -> Delivery:
        """Обновляет существующий адрес доставки.

        Args:
            instance: Объект Delivery для обновления.
            validated_data: Проверенные данные для обновления.
            user: Пользователь, выполняющий обновление.

        Returns:
            Обновленный объект Delivery.

        Raises:
            DeliveryServiceException: Если данные некорректны или обновление не удалось.
            DeliveryNotFound: Если адрес не существует.
        """
        user_id = user.id
        logger.info(f"Updating delivery {instance.id}, user={user_id}")
        try:
            if instance.user != user and not user.is_staff:
                logger.warning(f"Permission denied for delivery {instance.id}, user={user_id}")
                raise DeliveryServiceException("Только владелец или администратор может обновить адрес доставки.")

            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            logger.info(f"Updated delivery {instance.id}, user={user_id}")
            return instance
        except ValidationError as e:
            logger.error(f"Validation failed for delivery {instance.id}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка валидации адреса доставки: {str(e)}")
        except DatabaseError as e:
            logger.error(f"Database error updating delivery {instance.id}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка базы данных при обновлении адреса доставки: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating delivery {instance.id}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Неизвестная ошибка при обновлении адреса доставки: {str(e)}")

    @staticmethod
    @transaction.atomic
    def delete_delivery(instance: Delivery, user: User) -> None:
        """Удаляет адрес доставки.

        Args:
            instance: Объект Delivery для удаления.
            user: Пользователь, выполняющий удаление.

        Raises:
            DeliveryServiceException: Если удаление не удалось или пользователь не имеет прав.
            DeliveryNotFound: Если адрес не существует.
        """
        user_id = user.id
        logger.info(f"Deleting delivery {instance.id}, user={user_id}")
        try:
            if instance.user != user and not user.is_staff:
                logger.warning(f"Permission denied for delivery {instance.id}, user={user_id}")
                raise DeliveryServiceException("Только владелец или администратор может удалить адрес доставки.")
            instance.delete()
            logger.info(f"Deleted delivery {instance.id}, user={user_id}")
        except DatabaseError as e:
            logger.error(f"Database error deleting delivery {instance.id}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Ошибка базы данных при удалении адреса доставки: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting delivery {instance.id}: {str(e)}, user={user_id}")
            raise DeliveryServiceException(f"Неизвестная ошибка при удалении адреса доставки: {str(e)}")
