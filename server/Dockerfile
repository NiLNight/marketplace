# --- Этап 1: Builder ---
FROM python:3.12-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей
COPY requirements/base.txt /app/requirements/base.txt

# Устанавливаем зависимости в "колеса"
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r /app/requirements/base.txt


# --- Этап 2: Final ---
FROM python:3.12-slim

RUN groupadd -r marketplace && useradd --no-log-init -r -g marketplace marketplace

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем "колеса" и устанавливаем их
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

WORKDIR /app

# Копируем код приложения
COPY . .

# Установка прав на файлы
RUN chown -R marketplace:marketplace /app
USER marketplace

EXPOSE 8000