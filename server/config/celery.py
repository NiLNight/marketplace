"""Конфигурация Celery для проекта.

Определяет настройки Celery, включая очереди, маршрутизацию и параметры брокера.
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('marketplace')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Настройки очередей с RabbitMQ
app.conf.task_queues = {
    'high': {
        'exchange': 'high',
        'exchange_type': 'direct',
        'routing_key': 'high',
    },
    'default': {
        'exchange': 'default',
        'exchange_type': 'direct',
        'routing_key': 'default',
    },
    'low': {
        'exchange': 'low',
        'exchange_type': 'direct',
        'routing_key': 'low',
    }
}

# Маршрутизация задач по очередям
app.conf.task_routes = {
    'apps.orders.*': {'queue': 'high'},
    'apps.delivery.*': {'queue': 'high'},
    'apps.users.services.tasks.*': {'queue': 'high'},
    'apps.products.*': {'queue': 'default'},
    'apps.reviews.*': {'queue': 'default'},
    'apps.comments.*': {'queue': 'default'},
    'apps.wishlists.*': {'queue': 'low'},
    'apps.carts.*': {'queue': 'low'},
}

# Настройки выполнения задач
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_always_eager=False,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=20 * 60,  # 20 минут
    broker_connection_retry_on_startup=True,
)

# Периодические задачи
app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'apps.users.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=3, minute=0),  # Каждый день в 3:00
    },
    'update-product-ratings': {
        'task': 'apps.products.tasks.update_product_ratings',
        'schedule': crontab(hour='*/1'),  # Каждый час
    },
}
