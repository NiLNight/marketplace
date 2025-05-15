import logging
from smtplib import SMTPException

from celery import shared_task
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Сервис для отправки уведомлений пользователям.

    Предоставляет методы для асинхронной отправки email-уведомлений, связанных с заказами.

    Attributes:
        logger: Логгер для записи событий сервиса.
    """

    @staticmethod
    @shared_task(bind=True, autoretry_for=(SMTPException,), max_retries=3, retry_backoff=60)
    def send_notification_async(self, user_email: str, message: str, user_id: int = None) -> None:
        """
        Асинхронно отправляет уведомление на email пользователя.

        Проверяет корректность email и текста сообщения перед отправкой.
        Логирует успешное выполнение или повторные попытки.

        Args:
            self: Экземпляр задачи Celery для управления повторными попытками.
            user_email (str): Email-адрес получателя.
            message (str): Текст уведомления.
            user_id (int, optional): Идентификатор пользователя.

        Raises:
            ValidationError: Если email или сообщение некорректны.
            SMTPException: Если отправка email не удалась (повторяется до 3 раз с интервалом 60 секунд).
        """
        logger.debug(f"Starting task: send_notification to {user_email},"
                     f" task_id={self.request.id}")
        validator = EmailValidator(message=_("Некорректный формат email"))
        try:
            validator(user_email)
        except ValidationError as e:
            logger.warning(f"Invalid email {user_email}, user_id={user_id or 'unknown'},"
                           f" task_id={self.request.id}")
            raise ValidationError(str(e))
        if not message or not message.strip():
            logger.warning(f"Empty message for email={user_email},"
                           f" user_id={user_id or 'unknown'}, task_id={self.request.id}")
            raise ValidationError(_("Сообщение не может быть пустым"))

        logger.info(f"Task started: send_notification to {user_email}, "
                    f"user_id={user_id or 'unknown'}, task_id={self.request.id}")
        try:
            send_mail(
                subject=_("Уведомление о заказе"),
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            logger.info(f"Task {self.request.id} completed successfully: notification sent to"
                        f" {user_email}, user_id={user_id or 'unknown'}")
        except SMTPException as e:
            logger.error(f"Task {self.request.id} failed: failed to send notification to"
                         f" {user_email}, user_id={user_id or 'unknown'}: {str(e)}")
            raise self.retry(exc=e)

    @staticmethod
    def send_notification(user, message: str) -> None:
        """
        Инициирует асинхронную отправку уведомления пользователю.

        Проверяет наличие email и корректность сообщения.

        Args:
            user: Объект пользователя, содержащий email.
            message (str): Текст уведомления.

        Raises:
            ValidationError: Если email отсутствует или сообщение пустое.
        """
        logger.debug(f"Queueing notification for user={user.id}, email={user.email}")
        if not user.email:
            logger.warning(f"No email provided for user={user.id}")
            raise ValidationError(_("Email пользователя отсутствует"))
        if not message or not message.strip():
            logger.warning(f"Empty message for user={user.id}")
            raise ValidationError(_("Сообщение не может быть пустым"))
        NotificationService.send_notification_async.delay(user.email, message, user_id=user.id)
