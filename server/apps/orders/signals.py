from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.orders.services.notification_services import NotificationService


@receiver(pre_save, sender=Order)
def track_status(sender, instance, **kwargs):
    if instance.pk:  # Если объект уже существует
        instance.__original_status = Order.objects.get(pk=instance.pk).status
    else:  # Новый объект
        instance.__original_status = None


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created:
        NotificationService.send_notification(
            instance.user, f"Ваш заказ #{instance.id} создан"
        )
    elif hasattr(instance, "__original_status") and instance.status != instance.__original_status:
        if instance.status == 'delivered':
            print('1')
            NotificationService.send_notification(
                instance.user, f"Ваш заказ #{instance.id} доставлен!"
            )
        else:
            print('2')
            NotificationService.send_notification(
                instance.user, f"Статус заказа #{instance.id} изменен на {instance.status}"
            )
