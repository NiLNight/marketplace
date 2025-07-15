# deployment/docker/backend/Dockerfile

# --- Этап 1: 'base' ---
# Общая основа для development и production. Устанавливает системные зависимости и Python.
# Используем slim-образ для уменьшения размера.
FROM python:3.12-slim as base

# Устанавливаем переменные окружения для Python, чтобы избежать создания .pyc файлов
# и обеспечить немедленный вывод в логи, что критично для Docker.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера.
WORKDIR /app

# Обновляем пакетный менеджер и устанавливаем системные зависимости,
# необходимые для сборки некоторых Python-пакетов (например, psycopg для PostgreSQL).
# `--no-install-recommends` уменьшает количество ненужных пакетов.
# `rm -rf /var/lib/apt/lists/*` очищает кэш apt после установки.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Обновляем pip до последней версии для лучшей совместимости и безопасности.
RUN pip install --no-cache-dir --upgrade pip


# --- Этап 2: 'builder' ---
# Этот этап используется для сборки production-зависимостей.
# Это позволяет Docker кэшировать зависимости и значительно ускоряет последующие сборки,
# если файлы requirements не менялись.
FROM base as builder

# Копируем только файлы с зависимостями.
COPY requirements/ /app/requirements/

# Устанавливаем зависимости в формате "колес" (wheels). Это pre-compiled пакеты,
# которые устанавливаются быстрее, чем сборка из исходников.
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r /app/requirements/base.txt


# --- Этап 3: 'development' (Цель для разработки) ---
# Эта цель будет использоваться при запуске `docker-compose up` без указания prod-файла.
FROM base as development

# Копируем все файлы зависимостей.
COPY requirements/ /app/requirements/
# Устанавливаем все зависимости, включая dev-пакеты (pytest, debug-toolbar и т.д.).
RUN pip install --no-cache-dir -r /app/requirements/dev.txt

# Копируем весь код проекта. При использовании volumes в docker-compose этот шаг
# будет переопределен, но он нужен для первоначальной сборки.
COPY . .


# --- Этап 4: 'production' (Цель для продакшена) ---
# Эта цель создает оптимизированный и безопасный образ для деплоя.
FROM base as production

# Создаем непривилегированного пользователя и группу для запуска приложения.
# Запуск от root в продакшене — плохая практика безопасности.
RUN groupadd -r marketplace && useradd --no-log-init -r -g marketplace marketplace

# Копируем предустановленные "колеса" из этапа 'builder'.
# Это избавляет от необходимости заново компилировать пакеты.
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Устанавливаем рабочую директорию.
WORKDIR /app

# Копируем весь код приложения в контейнер.
COPY . .

# Меняем владельца всех файлов приложения на нашего непривилегированного пользователя.
RUN chown -R marketplace:marketplace /app

# Переключаемся на непривилегированного пользователя. Все последующие команды
# будут выполняться от его имени.
USER marketplace

# Запускаем приложение через Gunicorn.
# Конфигурация Gunicorn вынесена в отдельный файл для гибкости.
CMD ["gunicorn", "config.wsgi:application", "-c", "deployment/gunicorn/gunicorn.conf.py"]