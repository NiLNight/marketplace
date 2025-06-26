## Технический стек

- Python 3.11+
- Django 5.1+
- Django REST Framework (DRF)
- PostgreSQL 15+
- Redis 7+
- Celery 5+
- Elasticsearch 8+
- django-elasticsearch-dsl
- drf-spectacular (OpenAPI/Swagger)
- JWT (SimpleJWT)
- MPTT (иерархия категорий, комментариев)
- Pillow, pytils, shortuuid
- Black, Flake8, isort, mypy (линтеры и форматирование)

Полный список — в [requirements.txt](requirements.txt).

---

## Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/marketplace.git
   cd marketplace/server
   ```
2. Создайте виртуальное окружение и активируйте его:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate    # Windows
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте файл .env на основе .env.example и заполните своими значениями:
   ```bash
   cp .env.example .env
   ```
   **Ключевые переменные .env:**
    - SECRET_KEY
    - DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
    - REDIS_HOST, REDIS_PORT
    - ELASTICSEARCH_HOST, ELASTICSEARCH_PORT
    - EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

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

### Запуск сервисов

1. Запустите Redis и Elasticsearch (локально или через Docker).

```bash
   docker-compose up -d
   ```

2. Запустите Celery worker и beat:
   ```bash
   celery -A config worker -l debug --pool=solo
   ```
3. Запустите Django сервер:
   ```bash
   python manage.py runserver
   ```

### Docker (если используется)

1. Установите Docker и Docker Compose.
2. Запустите все сервисы:
   ```bash
   docker-compose up -d
   ```
3. Остановите сервисы:
   ```bash
   docker-compose down
   ```

---

## Структура проекта

- `apps/core/` — базовые сервисы, кэш, лайки, timestamp-модель
- `apps/users/` — регистрация, подтверждение email, JWT, профиль, сброс пароля
- `apps/products/` — товары, категории (MPTT), поиск (Elasticsearch), фильтрация, сортировка
- `apps/carts/` — корзина (авторизованные и гости), добавление/удаление/обновление товаров
- `apps/orders/` — оформление заказов, статусы, интеграция с доставкой
- `apps/delivery/` — города, пункты выдачи, поиск, фильтрация, интеграция с заказами
- `apps/reviews/` — отзывы к товарам, лайки, вложения, сортировка
- `apps/comments/` — древовидные комментарии к отзывам, лайки, вложенность
- `apps/wishlists/` — список желаемого (авторизованные и гости)
- `config/` — настройки, celery, urls, wsgi/asgi
- `requirements.txt`, `README.md`, `.env.example`, `docker-compose.yml` (если есть)

---

## Рекомендации по разработке

- Следуйте PEP 8, используйте типизацию, пишите документацию и тесты
- Используйте feature branches, Conventional Commits, проверяйте код линтером
- Не коммитьте .env файлы, используйте безопасные настройки в production
- Регулярно обновляйте зависимости

---

## Мониторинг и отладка

- Логи: `server/logs/app.log`, ротация логов
- Flower для мониторинга Celery задач
- Elasticsearch: http://localhost:9200
- Django Debug Toolbar (dev)

---

## Тестирование

- Покрытие тестами: сервисы, API, валидация, ошибки
- Запуск тестов:
  ```bash
  python manage.py test --keepdb
  ```

---

## Безопасность

- JWT, подтверждение email, ограничения на изменение критичных полей, rate limiting, CORS

---

## Кэширование и производительность

- Redis для кэша, оптимизация запросов (select_related, prefetch_related)

---

## Документация API

- drf-spectacular, OpenAPI/Swagger: `/api/schema/` (JSON), `/api/docs/` (Swagger UI)

---

**Вопросы и предложения:** создавайте issue или pull request.