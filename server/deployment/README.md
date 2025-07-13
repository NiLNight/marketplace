# 🚀 Деплой Marketplace Backend

Полное руководство по развертыванию Django приложения Marketplace в продакшене.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Архитектура](#архитектура)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Деплой](#деплой)
- [Мониторинг](#мониторинг)
- [Безопасность](#безопасность)
- [Устранение неполадок](#устранение-неполадок)

## ⚡ Быстрый старт

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd marketplace/server

# Создайте .env файл
cp deployment/env/env.development .env

# Настройте переменные окружения
nano .env
```

### 2. Запуск в режиме разработки

```bash
# Установите зависимости
pip install -r requirements/local.txt

# Запустите миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser

# Запустите сервер разработки
python manage.py runserver
```

### 3. Запуск с Docker

```bash
# Соберите и запустите контейнеры
docker-compose up -d

# Проверьте статус
docker-compose ps
```

## 🏗️ Архитектура

```
marketplace/
├── deployment/           # Файлы деплоя
│   ├── docker/          # Docker конфигурации
│   │   ├── backend/     # Backend образы
│   │   ├── nginx/       # Nginx конфигурации
│   │   └── prometheus/  # Мониторинг
│   ├── env/             # Переменные окружения
│   ├── gunicorn/        # Gunicorn конфигурации
│   └── scripts/         # Скрипты деплоя
├── apps/                # Django приложения
├── config/              # Настройки Django
├── requirements/         # Зависимости Python
└── logs/                # Логи приложения
```

### Компоненты системы

- **Django Backend** - Основное приложение
- **PostgreSQL** - База данных
- **Redis** - Кэширование и сессии
- **RabbitMQ** - Очереди для Celery
- **Elasticsearch** - Поиск и индексация
- **Nginx** - Веб-сервер и прокси
- **Gunicorn** - WSGI сервер
- **Celery** - Асинхронные задачи
- **Prometheus** - Мониторинг метрик
- **Grafana** - Визуализация метрик
- **Flower** - Мониторинг Celery

## 📋 Требования

### Системные требования

- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: Минимум 4GB, рекомендуется 8GB+
- **CPU**: 2+ ядра
- **Диск**: 20GB+ свободного места
- **Сеть**: Статический IP адрес

### Программное обеспечение

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.25+
- **Python**: 3.9+
- **Node.js**: 16+ (для фронтенда)

### Порты

| Сервис | Порт | Описание |
|--------|------|----------|
| Nginx | 80, 443 | Веб-сервер |
| Django | 8000 | Backend API |
| PostgreSQL | 5432 | База данных |
| Redis | 6379 | Кэш |
| RabbitMQ | 5672, 15672 | Очереди |
| Elasticsearch | 9200 | Поиск |
| Prometheus | 9090 | Метрики |
| Grafana | 3000 | Дашборды |
| Flower | 5555 | Celery мониторинг |

## 🔧 Установка

### 1. Подготовка сервера

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите необходимые пакеты
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установите Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузите систему
sudo reboot
```

### 2. Настройка файрвола

```bash
# Установите UFW
sudo apt install -y ufw

# Настройте правила
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp

# Включите файрвол
sudo ufw enable
```

### 3. Настройка SSL сертификатов

```bash
# Создайте директорию для сертификатов
mkdir -p deployment/ssl

# Для Let's Encrypt (рекомендуется)
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com

# Скопируйте сертификаты
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/ssl/marketplace.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/ssl/marketplace.key
sudo chown $USER:$USER deployment/ssl/*
```

## ⚙️ Конфигурация

### 1. Переменные окружения

Создайте файл `.env` на основе примера:

```bash
# Для разработки
cp deployment/env/env.development .env

# Для продакшена
cp deployment/env/env.production .env
```

### 2. Настройка базы данных

```bash
# Создайте базу данных
sudo -u postgres psql

CREATE DATABASE marketplace_prod;
CREATE USER marketplace_user WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE marketplace_prod TO marketplace_user;
ALTER USER marketplace_user CREATEDB;
\q
```

### 3. Генерация SECRET_KEY

```bash
# Сгенерируйте новый SECRET_KEY
python deployment/scripts/generate_secret_key.py

# Скопируйте результат в .env файл
```

## 🚀 Деплой

### Автоматический деплой

```bash
# Запустите полный деплой
./deployment/scripts/deploy.sh

# Или отдельные команды
./deployment/scripts/deploy.sh build    # Сборка образов
./deployment/scripts/deploy.sh migrate  # Миграции
./deployment/scripts/deploy.sh static   # Статические файлы
./deployment/scripts/deploy.sh health   # Проверка здоровья
```

### Ручной деплой

```bash
# 1. Остановите существующие контейнеры
docker-compose down

# 2. Соберите образы
docker-compose build --no-cache

# 3. Запустите сервисы
docker-compose up -d

# 4. Выполните миграции
docker-compose exec backend python manage.py migrate

# 5. Соберите статические файлы
docker-compose exec backend python manage.py collectstatic --noinput

# 6. Создайте суперпользователя
docker-compose exec backend python manage.py createsuperuser
```

### Проверка деплоя

```bash
# Проверьте статус контейнеров
docker-compose ps

# Проверьте логи
docker-compose logs

# Проверьте здоровье приложения
curl http://localhost:8000/health/

# Проверьте безопасность
python deployment/scripts/security_check.py
```

## 📊 Мониторинг

### Доступные дашборды

- **Grafana**: http://your-domain.com:3000
  - Логин: `admin`
  - Пароль: из переменной `GRAFANA_PASSWORD`

- **Prometheus**: http://your-domain.com:9090
  - Метрики производительности

- **Flower**: http://your-domain.com:5555
  - Мониторинг Celery задач

### Основные метрики

- **Производительность**: Время ответа, RPS
- **Ресурсы**: CPU, RAM, диск
- **База данных**: Подключения, запросы
- **Очереди**: Размер очередей, время обработки
- **Ошибки**: 4xx, 5xx статусы

### Алерты

Настройте алерты в Grafana для:
- Высокой нагрузки CPU (>80%)
- Нехватки памяти (>90%)
- Медленных запросов (>5s)
- Ошибок (>5%)

## 🔒 Безопасность

### Основные меры безопасности

1. **HTTPS**: Принудительное перенаправление на HTTPS
2. **HSTS**: HTTP Strict Transport Security
3. **CSP**: Content Security Policy
4. **Rate Limiting**: Ограничение запросов
5. **CORS**: Настройка Cross-Origin Resource Sharing
6. **SQL Injection**: Защита через ORM
7. **XSS**: Защита от межсайтового скриптинга
8. **CSRF**: Защита от подделки запросов

### Регулярные проверки

```bash
# Еженедельная проверка безопасности
python deployment/scripts/security_check.py

# Обновление зависимостей
pip install --upgrade -r requirements/base.txt

# Проверка уязвимостей
safety check

# Обновление SSL сертификатов
sudo certbot renew
```

### Резервное копирование

```bash
# Автоматическое резервное копирование
./deployment/scripts/deploy.sh backup

# Восстановление из резервной копии
docker-compose exec db psql -U marketplace_user -d marketplace_prod < backup.sql
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose logs

# Проверьте статус
docker-compose ps

# Перезапустите контейнеры
docker-compose restart
```

#### 2. Ошибки подключения к базе данных

```bash
# Проверьте настройки БД
docker-compose exec db psql -U marketplace_user -d marketplace_prod

# Проверьте переменные окружения
echo $DB_HOST $DB_NAME $DB_USER
```

#### 3. Проблемы с SSL

```bash
# Проверьте сертификаты
openssl x509 -in deployment/ssl/marketplace.crt -text -noout

# Обновите сертификаты
sudo certbot renew
```

#### 4. Высокая нагрузка

```bash
# Проверьте использование ресурсов
docker stats

# Увеличьте количество workers
# В .env файле: GUNICORN_WORKERS=8
```

### Полезные команды

```bash
# Просмотр логов в реальном времени
docker-compose logs -f

# Подключение к контейнеру
docker-compose exec backend bash

# Проверка сетевых подключений
docker network ls
docker network inspect marketplace_default

# Очистка неиспользуемых ресурсов
docker system prune -a
```

## 📞 Поддержка

### Логи и отладка

- **Логи приложения**: `logs/app.log`
- **Логи Nginx**: `/var/log/nginx/`
- **Логи Docker**: `docker-compose logs`

### Контакты

- **Документация**: [GitHub Wiki](https://github.com/your-repo/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discord**: [Сервер сообщества](https://discord.gg/your-server)

### Полезные ссылки

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)

---

**⚠️ Важно**: Всегда тестируйте изменения в staging окружении перед применением в продакшене! 