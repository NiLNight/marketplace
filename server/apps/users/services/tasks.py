from socket import gaierror
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(SMTPException, gaierror), max_retries=3)
def send_confirmation_email(self, email: str, code: str) -> None:
    """Отправляет письмо с кодом подтверждения на указанный email.

    Асинхронная задача Celery для отправки кода подтверждения.
    В случае ошибки отправки выполняется до 3 повторных попыток с интервалом 60 секунд.

    Args:
        self: Экземпляр задачи Celery.
        email (str): Адрес электронной почты получателя.
        code (str): Код подтверждения для отправки.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        SMTPException: Если отправка письма не удалась.
        gaierror: Если возникла ошибка DNS или сетевого соединения.
        ValidationError: Если формат email некорректен.
    """
    logger.info(f"Sending confirmation email to {email} with code={code}, task_id={self.request.id}")
    try:
        validate_email(email)
    except ValidationError:
        logger.error(f"Invalid email format: {email}, task_id={self.request.id}")
        return
    try:
        send_mail(
            subject="Ваш код подтверждения",
            message=f"Код: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f"Confirmation email sent to {email}, task_id={self.request.id}")
    except (SMTPException, gaierror) as e:
        logger.error(f"Failed to send confirmation email to {email}: {str(e)}, task_id={self.request.id}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, autoretry_for=(SMTPException, gaierror), max_retries=3)
def send_password_reset_email(self, email: str, reset_url: str) -> None:
    """Отправляет письмо для сброса пароля на указанный email.

    Асинхронная задача Celery для отправки ссылки сброса пароля.
    В случае ошибки отправки выполняется до 3 повторных попыток с интервалом 60 секунд.
    Проверяет длину URL для предотвращения слишком длинных ссылок.

    Args:
        self: Экземпляр задачи Celery.
        email (str): Адрес электронной почты получателя.
        reset_url (str): Ссылка для сброса пароля.

    Returns:
        None: Функция ничего не возвращает.

    Raises:
        SMTPException: Если отправка письма не удалась.
        gaierror: Если возникла ошибка DNS или сетевого соединения.
        ValidationError: Если формат email некорректен.
    """
    logger.info(f"Starting password reset email task for {email}, task_id={self.request.id}")
    
    logger.debug(f"Checking reset URL length: {len(reset_url)} characters")
    if len(reset_url) > 2000:
        logger.error(f"Reset URL too long: {len(reset_url)} characters, task_id={self.request.id}")
        return
        
    logger.debug(f"Validating email format: {email}")
    try:
        validate_email(email)
    except ValidationError:
        logger.error(f"Invalid email format: {email}, task_id={self.request.id}")
        return
        
    try:
        logger.debug(f"Preparing to send email to {email}")
        logger.debug(f"Using FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        send_mail(
            subject="Сброс пароля",
            message=f"Для сброса пароля перейдите по ссылке: {reset_url}",
            html_message=f"Для сброса пароля <a href='{reset_url}'>перейдите по ссылке</a>",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f"Password reset email successfully sent to {email}, task_id={self.request.id}")
    except (SMTPException, gaierror) as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}, task_id={self.request.id}")
        logger.debug(f"Will retry in 60 seconds, attempt {self.request.retries + 1} of 3")
        raise self.retry(exc=e, countdown=60)
    except Exception as e:
        logger.error(f"Unexpected error sending password reset email: {str(e)}, task_id={self.request.id}")
        raise
