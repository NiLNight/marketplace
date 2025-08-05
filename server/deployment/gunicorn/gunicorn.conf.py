"""
Конфигурация Gunicorn для продакшена.

Настройки безопасности и производительности для деплоя Django приложения.
"""

import os
import multiprocessing

# Базовые настройки
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Настройки безопасности
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Настройки логирования
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Настройки процесса
user = os.environ.get('GUNICORN_USER', 'marketplace')
group = os.environ.get('GUNICORN_GROUP', 'marketplace')
tmp_upload_dir = None

# Настройки SSL (если используется)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Настройки для продакшена
preload_app = True
daemon = False
pidfile = "/tmp/gunicorn.pid"
umask = 0o022

# Настройки worker'ов
worker_tmp_dir = "/dev/shm"
worker_exit_on_app_exit = True

# Настройки для мониторинга
enable_stdio_inheritance = True


def when_ready(server):
    """Вызывается когда сервер готов принимать запросы."""
    server.log.info("Gunicorn server is ready to accept connections")


def worker_int(worker):
    """Вызывается при получении SIGINT в worker."""
    worker.log.info("Worker received SIGINT")


def pre_fork(server, worker):
    """Вызывается перед созданием worker."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_fork(server, worker):
    """Вызывается после создания worker."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_worker_init(worker):
    """Вызывается после инициализации worker."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)


def worker_abort(worker):
    """Вызывается при аварийном завершении worker."""
    worker.log.info("Worker aborted (pid: %s)", worker.pid)


def post_request(worker, req, environ, resp):
    """Вызывается после обработки запроса."""
    worker.log.info(f"Request processed: {req.method} {req.path} -> {resp.status}")


# Настройки для мониторинга здоровья
def health_check(environ, start_response):
    """Простая проверка здоровья приложения."""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'OK']


# Дополнительные настройки безопасности
forwarded_allow_ips = '*'  # Настройте в соответствии с вашей инфраструктурой
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
