from smtplib import SMTPException
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def send_confirmation_email(self, email: str, code: str):
    """Отправляет email с кодом подтверждения.

    Args:
        email: Адрес получателя.
        code: Код подтверждения.

    Raises:
        SMTPException: Если отправка письма не удалась.
    """
    logger.info(f"Sending confirmation email to {email}, code={code}")
    try:
        send_mail(
            subject="Ваш код подтверждения",
            message=f"Код: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f"Confirmation email sent successfully to {email}")
    except SMTPException as e:
        logger.error(f"Failed to send confirmation email to {email}: {str(e)}")
        self.retry(exc=e, countdown=60)  # Повторить через 60 секунд


@shared_task(bind=True, autoretry_for=(Exception,))
def send_password_reset_email(self, email: str, reset_url: str):
    """Отправляет email со ссылкой для сброса пароля.

    Args:
        email: Адрес получателя.
        reset_url: Ссылка для сброса пароля.

    Raises:
        SMTPException: Если отправка письма не удалась.
    """
    logger.info(f"Sending password reset email to {email}, url={reset_url}")
    try:
        send_mail(
            subject="Сброс пароля",
            message=f"Для сброса пароля перейдите по ссылке: {reset_url}",
            html_message=f"Для сброса пароля <a href='{reset_url}'>перейдите по ссылке</a>",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        logger.info(f"Password reset email sent successfully to {email}")
    except SMTPException as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        self.retry(exc=e, countdown=60)  # Повторить через 60 секунд
