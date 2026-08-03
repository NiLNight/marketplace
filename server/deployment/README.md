# 🚀 Marketplace - Production & Deployment Guide

Полнофункциональный маркетплейс (Django REST Framework + React/Vite + PostgreSQL + Redis + RabbitMQ + Elasticsearch + Nginx).

---

## 📋 Содержание

- [Технический стек](#-технический-стек)
- [Структура проекта](#-структура-проекта)
- [Пошаговая инструкция по деплою (Production)](#-пошаговая-инструкция-по-деплою-production)
  - [Шаг 1. Подготовка VPS сервера](#шаг-1-подготовка-vps-сервера)
  - [Шаг 2. Клонирование репозитория](#шаг-2-клонирование-репозитория)
  - [Шаг 3. Выпуск SSL-сертификатов (Certbot)](#шаг-3-выпуск-ssl-сертификатов-certbot)
  - [Шаг 4. Настройка файла .env.prod](#шаг-4-настройка-файла-envprod)
  - [Шаг 5. Сборка фронтенда (React / Vite)](#шаг-5-сборка-фронтенда-react--vite)
  - [Шаг 6. Запуск Docker Compose](#шаг-6-запуск-docker-compose)
  - [Шаг 7. База данных и поисковый индекс Elasticsearch](#шаг-7-база-данных-и-поисковый-индекс-elasticsearch)
- [Полезные команды обслуживания](#-полезные-команды-обслуживания)
- [Глубокая очистка диска на VPS](#-глубокая-очистка-диска-на-vps)

---

## 🛠 Технический стек

- **Backend**: Python 3.12, Django 5.1, Django REST Framework, SimpleJWT, Celery
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS, Zustand
- **Базы данных и брокеры**: PostgreSQL 17, Redis 7, RabbitMQ 3.12
- **Поиск**: Elasticsearch 8 (с асинхронными сигналами Celery)
- **Веб-сервер & SSL**: Nginx (Reverse Proxy), Let's Encrypt (Certbot)
- **Email**: Resend SMTP

---

## 📂 Структура проекта

```
marketplace/
├── frontend/             # React SPA приложение
│   ├── src/
│   ├── .env              # VITE_API_BASE_URL=https://nilplace.space/
│   └── dist/             # Собранный продакшен-код фронтенда
└── server/               # Django REST API Бэкенд
    ├── apps/             # Модули приложения
    ├── config/           # Настройки Django, Celery, URLs
    ├── deployment/       # Конфигурации деплоя
    │   ├── docker/nginx/ # Nginx конфигурация
    │   └── ssl/          # Папка с SSL сертификатами
    ├── .env.prod         # Переменные окружения для продакшена
    └── docker-compose.prod.yml
```

---

## 🚀 Пошаговая инструкция по деплою (Production)

### Шаг 1. Подготовка VPS сервера

1. **Подключитесь к VPS по SSH:**
   ```bash
   ssh root@ВАШ_IP_СЕРВЕРА
   ```

2. **Обновите систему и установите базовные утилиты:**
   ```bash
   apt update && apt upgrade -y
   apt install -y git docker.io docker-compose-v2 curl
   systemctl enable --now docker
   ```

3. **Оптимизация памяти ядра для Elasticsearch (Обязательно для Linux):**
   ```bash
   sysctl -w vm.max_map_count=262144
   echo "vm.max_map_count=262144" >> /etc/sysctl.conf
   ```

---

### Шаг 2. Клонирование репозитория

```bash
mkdir -p /var/www && cd /var/www
git clone https://github.com/NiLNight/marketplace.git
cd marketplace
```

---

### Шаг 3. Выпуск SSL-сертификатов (Certbot)

1. Убедитесь, что `A`-записи вашего домена (например, `nilplace.space` и `www.nilplace.space`) смотрят на IP вашего VPS.
2. Установите Certbot и выпустите сертификат:
   ```bash
   apt install -y certbot
   certbot certonly --standalone -d nilplace.space -d www.nilplace.space
   ```
3. Скопируйте сертификаты в папку проекта (`-L` критически важен для копирования реальных файлов вместо симлинков):
   ```bash
   cd /var/www/marketplace/server
   mkdir -p deployment/ssl
   cp -L /etc/letsencrypt/live/nilplace.space/fullchain.pem deployment/ssl/fullchain.pem
   cp -L /etc/letsencrypt/live/nilplace.space/privkey.pem deployment/ssl/privkey.pem
   ```

---

### Шаг 4. Настройка файла `.env.prod`

Создайте файл `/var/www/marketplace/server/.env.prod`:

```bash
cat > .env.prod << 'EOF'
# Django Settings
SECRET_KEY="сгенерированный_секретный_ключ"
DEBUG=False
ENVIRONMENT=production
ALLOWED_HOSTS="nilplace.space,www.nilplace.space,backend,nginx,localhost"

# Database Settings
DB_ENGINE='django.db.backends.postgresql'
DB_HOST="db"
DB_PORT='5432'
DB_NAME='marketplace_prod'
DB_USER='marketplace_user'
DB_PASS='ваш_надежный_пароль_бд'

# Redis & RabbitMQ
REDIS_HOST='redis'
REDIS_PORT='6379'
REDIS_PASSWORD='ваш_пароль_redis'
RABBITMQ_HOST='rabbitmq'
RABBITMQ_PORT='5672'

# Elasticsearch Settings
ELASTICSEARCH_HOSTS='http://elasticsearch:9200'

# Email Settings (Resend SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=re_ВАШ_API_KEY_RESEND

# Важно: используйте кавычки для строк с символами < >
DEFAULT_FROM_EMAIL="Marketplace <onboarding@resend.dev>"
SERVER_EMAIL="Marketplace <onboarding@resend.dev>"

# Frontend URL
FRONTEND_URL="https://nilplace.space"
EOF
```

---

### Шаг 5. Сборка фронтенда (React / Vite)

1. **Установите Node.js 20:**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
   apt install -y nodejs
   ```

2. **Создайте `.env` во фронтенде:**
   ```bash
   cd /var/www/marketplace/frontend
   echo "VITE_API_BASE_URL=https://nilplace.space/" > .env
   ```

3. **Соберите фронтенд:**
   ```bash
   npm install
   npx vite build
   ```
   *(Результат сборки появится в `frontend/dist`)*.

---

### Шаг 6. Запуск Docker Compose

В папке `/var/www/marketplace/server` выполните запуск продакшен-инфраструктуры:

```bash
cd /var/www/marketplace/server
docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml up -d
```

Проверьте статус всех контейнеров (все 9 должны быть `Up` / `Healthy`):
```bash
docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml ps
```

---

### Шаг 7. База данных и поисковый индекс Elasticsearch

1. **Примените миграции базы данных:**
   ```bash
   docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py migrate
   ```

2. **Создайте пользователя Администратора:**
   ```bash
   docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py createsuperuser
   ```

3. **Восстановление дампа PostgreSQL (если есть дамп):**
   ```bash
   # Копируем дамп в контейнер
   docker cp /tmp/marketplace_dump.sqlc marketplace-db-prod:/tmp/marketplace_dump.sqlc
   
   # Восстанавливаем
   docker exec -t marketplace-db-prod pg_restore -U marketplace_user -d marketplace_prod --clean --no-acl --no-owner /tmp/marketplace_dump.sqlc
   ```

4. **Инициализация поиска Elasticsearch:**
   ```bash
   # Отключаем контроль порога диска для стабильности
   docker exec marketplace-elasticsearch-prod curl -X PUT "http://localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{"transient": {"cluster.routing.allocation.disk.threshold_enabled": false}}'
   
   # Создаем и наполняем индексы
   docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py search_index --create
   docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py search_index --populate
   ```

---

## ⚙️ Полезные команды обслуживания

* **Перезапустить сервисы без пересборки (1 секунда, 0 МБ диска):**
  ```bash
  docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml restart backend celery
  ```

* **Просмотр логов в реальном времени:**
  ```bash
  docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml logs -f backend
  docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml logs -f celery
  ```

* **Проверка доступности здравоохранения (Healthcheck):**
  ```bash
  curl https://nilplace.space/core/health/
  ```

---

## 🧹 Глубокая очистка диска на VPS

Если на VPS с неболшим диском (10 ГБ) заканчивается место, выполните этот безопасный комплекс очистки:

```bash
# 1. Очищаем журнал системных логов Ubuntu
journalctl --vacuum-time=1d
journalctl --vacuum-size=50M

# 2. Очищаем кеш пакетов APT
apt autoremove -y && apt clean && rm -rf /var/lib/apt/lists/*

# 3. Полная очистка неиспользуемых слоев и кеша Docker
docker system prune -a --volumes -f
docker builder prune -a -f
```
