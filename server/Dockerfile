FROM python:3.12-slim as builder

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Финальный этап
FROM python:3.12-slim

# Создание непривилегированного пользователя
RUN groupadd -r marketplace && useradd -r -g marketplace marketplace

# Установка рабочей директории
WORKDIR /app

# Копирование установленных пакетов и бинарных файлов из builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Копирование кода проекта
COPY . .

# Установка прав на файлы
RUN chown -R marketplace:marketplace /app

# Переключение на непривилегированного пользователя
USER marketplace

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONDONTWRITEBYTECODE=1

# Порт для Django
EXPOSE 8000 