from celery import shared_task
from django.core.mail import send_mail

from config import settings


class NotificationService:
    @staticmethod
    @shared_task
    def send_notification_async(user_email: str, message: str):
        send_mail(
            subject="Уведомление о заказе",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )

    @staticmethod
    def send_notification(user, message: str):
        NotificationService.send_notification_async.delay(user.email, message)