# 🚀 Marketplace - Backend API

Полнофункциональный backend для маркетплейса с современным стеком технологий.

## 📋 Содержание

- [Технический стек](#технический-стек)
- [Быстрый старт](#быстрый-старт)
- [Установка и настройка](#установка-и-настройка)
- [Структура проекта](#структура-проекта)
- [Разработка](#разработка)
- [Продакшен](#продакшен)
- [Безопасность](#безопасность)
- [Мониторинг](#мониторинг)
- [Тестирование](#тестирование)
- [Документация API](#документация-api)

## 🛠️ Технический стек

### Основные технологии
- **Python 3.11+** - основной язык
- **Django 5.1+** - веб-фреймворк
- **Django REST Framework** - API
- **PostgreSQL 17+** - основная база данных
- **Redis 7+** - кэширование и сессии
- **Celery 5+** - асинхронные задачи
- **Elasticsearch 8+** - полнотекстовый поиск

### Дополнительные компоненты
- **django-elasticsearch-dsl** - интеграция с Elasticsearch
- **drf-spectacular** - OpenAPI/Swagger документация
- **JWT (SimpleJWT)** - аутентификация
- **MPTT** - иерархия категорий и комментариев
- **Pillow, pytils, shortuuid** - утилиты
- **Black, Flake8, isort, mypy** - линтеры и форматирование

Полный список зависимостей — в [requirements.txt](requirements/base.txt).

## ⚡ Быстрый старт

### Предварительные требования

- **Docker** и **Docker Compose** установлены
- **Git** для клонирования репозитория
- **Python 3.8+** (для локальной разработки)

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/marketplace.git
cd marketplace/server
```

### 2. Создание файлов переменных окружения

```bash
# Автоматическое создание .env с генерацией SECRET_KEY
python deployment/scripts/generate_secret_key.py
```

Скрипт автоматически:
- Генерирует безопасный SECRET_KEY
- Создает .env файл с базовыми настройками
- Предлагает настроить дополнительные параметры

### 3. Запуск с Docker

```bash
# Для разработки
docker-compose up -d

# Для продакшена
docker-compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml up -d 
```

### 4. Проверка работоспособности

```bash
# Проверка статуса контейнеров
docker-compose ps

# Проверка логов
docker-compose logs

# Проверка безопасности
python deployment/scripts/security_check.py
```

## 🔧 Установка и настройка

### Вариант 1: Docker (рекомендуется)

#### Настройка .env файла

```bash
# Создайте .env файл для разработки
cat > .env << 'EOF'
# Django Settings
SECRET_KEY="your-secret-key-here"
DEBUG=True
ENVIRONMENT=development

# Database Settings
DB_ENGINE='django.db.backends.postgresql'
DB_USER='marketplace'
DB_PASS='marketplace_dev_password_123'
DB_HOST='db'
DB_PORT='5432'
DB_NAME='marketplace'

# Redis Settings
REDIS_HOST='redis'
REDIS_PORT='6379'

# RabbitMQ Settings
RABBITMQ_HOST='rabbitmq'
RABBITMQ_PORT='5672'

# Elasticsearch Settings
ELASTICSEARCH_HOSTS='http://elasticsearch:9200'
ELASTICSEARCH_PASSWORD=''

# Email Settings
EMAIL_HOST_USER='dev@marketplace.local'
EMAIL_HOST_PASSWORD='dev_email_password_123'

# Frontend URL
FRONTEND_URL='http://localhost:5173'

# Grafana Password
GRAFANA_PASSWORD='admin123'
EOF
```

> **Примечание**: Документацию и настройку фронтенда см. в [../frontend/README.md](../frontend/README.md).

#### Запуск сервисов

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Логи в реальном времени
docker-compose logs -f
```

### Вариант 2: Локальная разработка

#### 1. Создание виртуального окружения

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

#### 2. Установка зависимостей

```bash
pip install -r requirements/local.txt
```

#### 3. Настройка базы данных

```bash
# Создайте базу данных PostgreSQL
createdb marketplace_dev

# Создайте пользователя (если нужно)
createuser marketplace_user
```

#### 4. Обновление индексов ElasticSearch
```bash
# Перестройка индексов ElasticSearch
docker-compose exec backend python manage.py search_index --rebuild
```


#### 5. Создание .env файла

```bash
# Скопируйте пример
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

**Ключевые переменные .env:**
- `SECRET_KEY` - секретный ключ Django
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` - настройки БД
- `REDIS_HOST`, `REDIS_PORT` - настройки Redis
- `ELASTICSEARCH_HOSTS` - настройки Elasticsearch
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - настройки email

#### 6. Применение миграций

```bash
python manage.py migrate
```

#### 7. Создание суперпользователя

```bash
python manage.py createsuperuser
```

#### 8. Сборка статических файлов

```bash
python manage.py collectstatic
```

#### 9. Перенос данных

```bash
# Создание дампа
"E:\PostgreSQL\17\bin\pg_dump.exe" -U marketplace -h localhost -p 5432 -d marketplace -F c -b -v -f marketplace_dump.sqlc

# Перенос дампа в докер
docker cp marketplace_dump.sqlc marketplace-db:/tmp/marketplace_dump.sqlc

# Восстановление из дампа
docker-compose exec -T db pg_restore -U marketplace -d marketplace --clean --no-acl --no-owner /tmp/marketplace_dump.sqlc
```

#### 10. Запуск сервисов

```bash
# Запустите Redis и Elasticsearch (локально или через Docker)
docker-compose up -d redis elasticsearch

# Запустите Celery worker
celery -A config worker -l debug --pool=solo

# Запустите Django сервер
python manage.py runserver
```

## 🏗️ Структура проекта

```
server/
├── apps/
│   ├── core/           # Базовые сервисы, кэш, лайки, timestamp-модель
│   ├── users/          # Регистрация, подтверждение email, JWT, профиль
│   ├── products/       # Товары, категории (MPTT), поиск (Elasticsearch)
│   ├── carts/          # Корзина (авторизованные и гости)
│   ├── orders/         # Оформление заказов, статусы, интеграция с доставкой
│   ├── delivery/       # Города, пункты выдачи, поиск, фильтрация
│   ├── reviews/        # Отзывы к товарам, лайки, вложения
│   ├── comments/       # Древовидные комментарии к отзывам
│   └── wishlists/      # Список желаемого (авторизованные и гости)
├── config/             # Настройки, celery, urls, wsgi/asgi
├── deployment/         # Скрипты деплоя, конфигурации
├── requirements/       # Зависимости для разных окружений
├── logs/              # Логи приложения
├── media/             # Загруженные файлы
├── static/            # Статические файлы
└── templates/         # Шаблоны
```

## 🔧 Разработка

### Полезные команды

```bash
# Запуск Django shell
docker-compose exec backend python manage.py shell

# Создание миграций
docker-compose exec backend python manage.py makemigrations

# Применение миграций
docker-compose exec backend python manage.py migrate

# Перестройка индексов ElasticSearch
docker-compose exec backend python manage.py search_index --rebuild

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Сборка статических файлов
docker-compose exec backend python manage.py collectstatic

# Запуск тестов
docker-compose exec backend python manage.py test --keepdb
```

### Мониторинг и отладка

```bash
# Статус контейнеров
docker-compose ps

# Логи конкретного сервиса
docker-compose logs backend
docker-compose logs celery
docker-compose logs db

# Перезапуск сервиса
docker-compose restart backend

# Остановка всех сервисов
docker-compose down

# Просмотр ресурсов
docker stats
```

### Доступные сервисы

После запуска будут доступны:

- **Приложение**: http://localhost:8000
- **Админка**: http://localhost:8000/admin/
- **API документация**: http://localhost:8000/api/swagger/
- **Elasticsearch**: http://localhost:9200
- **Flower (Celery)**: http://localhost:5555

## 🚀 Продакшен

### Настройка .env.prod

```bash
# Создайте файл .env.prod
cat > .env.prod << 'EOF'
# Django Settings
SECRET_KEY="your-production-secret-key-here"
DEBUG=False
ENVIRONMENT=production

# Database Settings
DB_ENGINE='django.db.backends.postgresql'
DB_HOST='postgres'
DB_PORT='5432'
DB_NAME='marketplace_prod'
DB_USER='marketplace_user'
DB_PASS='your-strong-production-password'

# Redis Settings
REDIS_HOST='redis'
REDIS_PORT='6379'

# RabbitMQ Settings
RABBITMQ_HOST='rabbitmq'
RABBITMQ_PORT='5672'

# Elasticsearch Settings
ELASTICSEARCH_HOSTS='elasticsearch:9200'

# Email Settings
EMAIL_HOST_USER='prod@example.com'
EMAIL_HOST_PASSWORD='your-production-email-password'

# Frontend URL
FRONTEND_URL='https://marketplace.example.com'

# Grafana Password
GRAFANA_PASSWORD='secure_production_password'
EOF
```

### Запуск продакшена

```bash
# Запуск продакшен окружения
docker-compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml up -d 

# Запуск и сборка продакшен окружения
docker-compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml up --build -d

# Проверка статуса
docker-compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml ps

# Логи в реальном времени
docker-compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml logs -f
```

### Продакшен сервисы

- **Приложение**: https://your-domain.com
- **Nginx**: http://localhost:80, https://localhost:443
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Flower**: http://localhost:5555

## 🔐 Безопасность

### Генерация SECRET_KEY

```bash
# Генерация безопасного ключа
python deployment/scripts/generate_secret_key.py
```

### Проверка безопасности

```bash
# Полная проверка безопасности
python deployment/scripts/security_check.py
```

### Защита файлов

```bash
# Добавьте в .gitignore
echo ".env" >> .gitignore
echo ".env.prod" >> .gitignore
echo "*.env" >> .gitignore
```

### Рекомендации безопасности

1. **Никогда не коммитьте .env файлы в git**
2. **Используйте разные SECRET_KEY для разработки и продакшена**
3. **Регулярно обновляйте зависимости**
4. **Мониторьте логи на предмет ошибок**
5. **Делайте резервные копии базы данных**

## 📊 Мониторинг

### Логирование

- Логи: `server/logs/app.log`
- Ротация логов настроена
- Django Debug Toolbar (только в development)

### Мониторинг Celery

- **Flower**: http://localhost:5555 - веб-интерфейс для мониторинга задач
- Логи Celery в реальном времени

### Мониторинг производительности

- **Prometheus**: метрики приложения
- **Grafana**: визуализация метрик
- **Elasticsearch**: мониторинг поиска

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
python manage.py test --keepdb

#Для продакшена
docker-compose -p server_prod -f docker-compose.prod.yml exec backend python manage.py test --keepdb

# Конкретное приложение
python manage.py test apps.users

# С покрытием
coverage run --source='.' manage.py test
coverage report
```

### Покрытие тестами

- Сервисы и бизнес-логика
- API endpoints
- Валидация данных
- Обработка ошибок
- Интеграционные тесты

## 📚 Документация API

### Swagger UI

- **URL**: http://localhost:8000/api/swagger/
- Интерактивная документация API
- Возможность тестирования endpoints

### OpenAPI Schema

- **URL**: http://localhost:8000/api/schema/
- JSON схема для интеграции

### Автоматическая генерация

Документация генерируется автоматически с помощью `drf-spectacular` на основе:
- Сериализаторов
- ViewSets и APIViews
- Документации в коде

## 🛠️ Устранение неполадок

### Проблема: "SECRET_KEY not set"

```bash
# Создайте .env файл
python deployment/scripts/generate_secret_key.py
```

### Проблема: "Database connection failed"

```bash
# Проверьте настройки БД
cat .env | grep DB_

# Перезапустите базу данных
docker-compose restart db
```

### Проблема: "Redis connection failed"

```bash
# Проверьте настройки Redis
cat .env | grep REDIS

# Перезапустите Redis
docker-compose restart redis
```

### Проблема: "Elasticsearch connection failed"

```bash
# Проверьте настройки Elasticsearch
cat .env | grep ELASTICSEARCH

# Перезапустите Elasticsearch
docker-compose restart elasticsearch
```

### Проблема: "Port already in use"

```bash
# Проверьте занятые порты
netstat -tulpn | grep :8000

# Остановите конфликтующие сервисы
sudo systemctl stop apache2  # если Apache использует порт 80
sudo systemctl stop nginx     # если Nginx использует порт 80
```

## 🔄 Обновление проекта

### Обновление кода

```bash
# Получите последние изменения
git pull origin main

# Пересоберите образы
docker-compose build --no-cache

# Перезапустите сервисы
docker-compose up -d
```

### Обновление зависимостей

```bash
# Обновите requirements
pip install -r requirements/local.txt

# Пересоберите образ
docker-compose build backend

# Перезапустите backend
docker-compose restart backend
```

## 🎯 Следующие шаги

1. **Настройте домен** для продакшена
2. **Настройте SSL сертификаты** (Let's Encrypt)
3. **Настройте мониторинг** (Prometheus + Grafana)
4. **Настройте резервное копирование** базы данных
5. **Настройте CI/CD** для автоматического деплоя

## 📞 Поддержка

- **Документация**: `README.md`
- **Деплой**: `DEPLOYMENT.md`
- **Проверка безопасности**: `python deployment/scripts/security_check.py`
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

## 🚨 Важные замечания

1. **Никогда не коммитьте .env файлы в git**
2. **Используйте разные SECRET_KEY для разработки и продакшена**
3. **Регулярно обновляйте зависимости**
4. **Мониторьте логи на предмет ошибок**
5. **Делайте резервные копии базы данных**

---

**🎉 Поздравляем!** Ваш проект Marketplace успешно настроен и готов к разработке!

**💡 Совет**: Регулярно обновляйте зависимости и проверяйте безопасность системы.