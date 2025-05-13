import logging
from celery import shared_task
from django.core.mail import send_mail
from smtplib import SMTPException
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений пользователям.

    Предоставляет методы для асинхронной отправки email-уведомлений, связанных с заказами.
    """

    @staticmethod
    @shared_task(bind=True, autoretry_for=(SMTPException,), max_retries=3, retry_backoff=60)
    def send_notification_async(self, user_email: str, message: str) -> None:
        """Асинхронная отправка уведомления на email пользователя.

        Args:
            self: Экземпляр задачи Celery для управления повторными попытками.
            user_email (str): Email-адрес получателя.
            message (str): Текст уведомления.

        Raises:
            SMTPException: Если произошла ошибка при отправке email, задача будет повторена.
        """
        logger.info(f"Sending notification to {user_email}")
        try:
            send_mail(
                subject="Уведомление о заказе",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            logger.info(f"Notification successfully sent to {user_email}")
        except SMTPException as e:
            logger.error(f"Failed to send notification to {user_email}: {str(e)}")
            raise self.retry(exc=e)

    @staticmethod
    def send_notification(user, message: str) -> None:
        """Инициирует асинхронную отправку уведомления пользователю.

        Args:
            user: Объект пользователя, содержащий email.
            message (str): Текст уведомления.
        """
        logger.debug(f"Queueing notification for user={user.id}, email={user.email}")
        if not user.email:
            logger.warning(f"No email provided for user={user.id}")
            return
        NotificationService.send_notification_async.delay(user.email, message)
