# Marketplace

Проект маркетплейса на Django REST Framework.

## Требования

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8+

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/marketplace.git
cd marketplace/server
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env на основе .env.example и заполните его своими значениями:
```bash
cp .env.example .env
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Соберите статические файлы:
```bash
python manage.py collectstatic
```

## Запуск

1. Запустите Redis:
```bash
redis-server
```

2. Запустите Elasticsearch:
```bash
elasticsearch
```

3. Запустите Celery worker:
```bash
celery -A config worker -l info
```

4. Запустите Celery beat:
```bash
celery -A config beat -l info
```

5. Запустите Flower для мониторинга Celery (опционально):
```bash
celery -A config flower
```

6. Запустите Django сервер:
```bash
python manage.py runserver
```

## Запуск с Docker

1. Установите Docker и Docker Compose

2. Запустите все сервисы:
```bash
docker-compose up -d
```

3. Проверьте статус сервисов:
```bash
docker-compose ps
```

4. Остановите сервисы:
```bash
docker-compose down
```

5. Просмотр логов:
```bash
docker-compose logs -f
```

### Переменные окружения для Docker

При использовании Docker, в файле .env нужно указать следующие значения:
```
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
REDIS_HOST=redis
REDIS_PORT=6379
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
```

## Структура проекта

- `apps/`