from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def send_confirmation_email(self, email: str, code: str):
    """Отправка письма с кодом подтверждения.

    Args:
        email (str): Адрес электронной почты получателя.
        code (str): Код подтверждения.

    Raises:
        SMTPException: Если отправка письма не удалась, повторяется через 60 секунд.
    """
    logger.info(f"Sending confirmation email to {email} with code={code}")
    try:
        send_mail(
            subject="Ваш код подтверждения",
            message=f"Код: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        logger.info(f"Confirmation email sent to {email}")
    except SMTPException as e:
        logger.error(f"Failed to send confirmation email to {email}: {str(e)}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, autoretry_for=(Exception,))
def send_password_reset_email(self, email: str, reset_url: str):
    """Отправка письма для сброса пароля.

    Args:
        email (str): Адрес электронной почты получателя.
        reset_url (str): Ссылка для сброса пароля.

    Raises:
        SMTPException: Если отправка письма не удалась, повторяется через 60 секунд.
    """
    logger.info(f"Sending password reset email to {email} with reset_url={reset_url}")
    try:
        send_mail(
            subject="Сброс пароля",
            message=f"Для сброса пароля перейдите по ссылке: {reset_url}",
            html_message=f"Для сброса пароля <a href='{reset_url}'>перейдите по ссылке</a>",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        logger.info(f"Password reset email sent to {email}")
    except SMTPException as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        self.retry(exc=e, countdown=60)
