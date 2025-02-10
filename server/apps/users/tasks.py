from smtplib import SMTPException

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=300)
def send_confirmation_email(self, email: str, code: str):
    print('Письмо отправлено')
    try:
        send_mail(
            subject="Ваш код подтверждения",
            message=f"Код: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
    except SMTPException as e:
        self.retry(exc=e, countdown=60)  # Повторить через 60 секунд
