# --- Этап 1: Builder ---
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем системные зависимости для сборки
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip до последней версии
RUN pip install --no-cache-dir --upgrade pip

# Копируем только файлы зависимостей
COPY ../../../requirements/base.txt /app/requirements/base.txt

# Устанавливаем зависимости в "колеса"
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r /app/requirements/base.txt

# --- Этап 2: Final ---
FROM python:3.12-slim

# Создаем пользователя и группу для безопасности
RUN groupadd -r marketplace && useradd --no-log-init -r -g marketplace marketplace

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копируем "колеса" и устанавливаем их
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

WORKDIR /app

# Копируем код приложения
COPY ../../.. .

# Копируем конфигурации
COPY nginx.conf /etc/nginx/nginx.conf
COPY ../../gunicorn/gunicorn.conf.py /app/gunicorn.conf.py

# Создаем необходимые директории
RUN mkdir -p /app/static /app/media /app/logs /var/log/nginx /var/cache/nginx

# Устанавливаем права на файлы
RUN chown -R marketplace:marketplace /app /var/log/nginx /var/cache/nginx

# Создаем символические ссылки для nginx
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Создаем health check endpoint
RUN echo 'from django.http import HttpResponse\n\
def health_check(request):\n\
    return HttpResponse("OK", content_type="text/plain")' > /app/health_check.py

# Создаем скрипт запуска
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Running database migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput --clear\n\
\n\
echo "Starting Nginx..."\n\
nginx -g "daemon off;" &\n\
\n\
echo "Starting Gunicorn..."\n\
exec gunicorn config.wsgi:application -c gunicorn.conf.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Переключаемся на непривилегированного пользователя
USER marketplace

# Открываем порты
EXPOSE 80 443 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Запускаем приложение
CMD ["/app/start.sh"]