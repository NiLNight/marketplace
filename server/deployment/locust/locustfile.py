import random
from locust import HttpUser, task, between, events
import os
import django
import urllib3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Отключаем предупреждения о небезопасных SSL-соединениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv

load_dotenv(dotenv_path=PROJECT_ROOT / '.env.locust')

# Это нужно, чтобы мы могли использовать Django ORM для получения случайных данных
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.products.models import Product, Category
from apps.reviews.models import Review
from django.contrib.auth import get_user_model

User = get_user_model()
PRODUCT_IDS = list(Product.objects.filter(is_active=True).values_list('id', flat=True))
CATEGORY_IDS = list(Category.objects.all().values_list('id', flat=True))
REVIEW_IDS = list(Review.objects.all().values_list('id', flat=True))


class GuestUser(HttpUser):
    """
    Поведение анонимного пользователя, который просто просматривает сайт.
    """
    wait_time = between(1, 5)  # Пауза между действиями от 1 до 5 секунд

    # Указываем базовый URL для тестирования Docker-сборки
    verify = False

    def on_start(self):
        """Настройка HTTP-клиента для игнорирования SSL-сертификатов"""
        self.client.verify = False

    @task(5)  # 5 раз важнее, чем другие задачи
    def view_products(self):
        # Переход по страницам каталога
        page = random.randint(1, 5)
        self.client.get(f"/products/list/", name="/products/list")

    @task(3)
    def view_product_detail(self):
        if PRODUCT_IDS:
            product_id = random.choice(PRODUCT_IDS)
            self.client.get(f"/products/{product_id}/", name="/products/[id]")
            # Также смотрим отзывы к этому товару
            self.client.get(f"/reviews/{product_id}/", name="/reviews/[product_id]")

    @task(1)
    def view_categories(self):
        self.client.get("/products/categories/")
        if CATEGORY_IDS:
            category_id = random.choice(CATEGORY_IDS)
            self.client.get(f"/products/categories/{category_id}/", name="/products/categories/[id]")


class AuthenticatedUser(HttpUser):
    """
    Базовый класс для залогиненного пользователя.
    Выполняет вход один раз при старте.
    """
    abstract = True  # Этот класс не будет запускаться сам по себе

    # Указываем базовый URL для тестирования Docker-сборки
    verify = False

    def on_start(self):
        """Выполняется один раз при старте "виртуального пользователя" """
        # Настройка HTTP-клиента для игнорирования SSL-сертификатов
        self.client.verify = False

        # Для тестов можно использовать одного и того же пользователя
        # В реальном нагрузочном тесте лучше создавать/использовать разных
        self.email = "bkmz-2020@inbox.ru"
        self.password = "test123456"  # <-- ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ПАРОЛЬ
        self.username = "nil"
        self.user_id = 16

        self.login()

        self.products_to_review = set(PRODUCT_IDS)  # Создаем копию для этого юзера

    def login(self):
        response = self.client.post("/user/login/", {
            "email": self.email,
            "password": self.password
        })
        if response.status_code == 200:
            self.user_id = response.json().get("user", {}).get("id")
        else:
            # Если логин не удался, можно попробовать зарегистрироваться
            self.client.post("/user/register/", {
                "username": f"{self.username}_{random.randint(1, 10000)}",
                "email": f"test_{random.randint(1, 10000)}@example.com",
                "password": self.password
            })
            # При реальном тесте здесь нужно было бы еще подтвердить email


class BuyerUser(AuthenticatedUser):
    """
    Поведение "Покупателя". Наследует логин от AuthenticatedUser.
    """
    wait_time = between(2, 6)

    verify = False

    def on_start(self):
        """Настройка HTTP-клиента для игнорирования SSL-сертификатов"""
        self.client.verify = False
        super().on_start()

    @task(10)
    def view_and_interact_with_products(self):
        # Выполняет те же действия, что и гость
        GuestUser.view_products(self)
        GuestUser.view_product_detail(self)

        if PRODUCT_IDS:
            product_id = random.choice(PRODUCT_IDS)
            # Добавляем в корзину
            self.client.post("/carts/add/", json={"product_id": product_id, "quantity": 1}, name="/carts/add")
            # Добавляем в список желаний
            self.client.post("/wishlists/add/", json={"product_id": product_id}, name="/wishlists/add")

    @task(2)
    def view_cart_and_wishlist(self):
        self.client.get("/carts/", name="/carts/")
        self.client.get("/wishlists/", name="/wishlists/")

    @task(1)
    def leave_review_and_comment(self):
        if self.products_to_review and REVIEW_IDS:
            product_id_to_review = random.choice(list(self.products_to_review))
            review_id = random.choice(REVIEW_IDS)

            # Оставляем отзыв
            with self.client.post("/reviews/create/", json={
                "product": product_id_to_review,
                "value": random.randint(3, 5),
                "text": "This is a test review from Locust."
            }, name="/reviews/create", catch_response=True) as response:
                if response.status_code == 201:
                    # Если отзыв успешно создан, удаляем этот товар из списка доступных для отзыва
                    self.products_to_review.remove(product_id_to_review)
                    response.success()
                else:
                    # Если получили ошибку (например, кто-то другой успел оставить отзыв),
                    # все равно удаляем товар из списка, чтобы не пытаться снова
                    self.products_to_review.remove(product_id_to_review)
                    response.failure(f"Could not create review, status {response.status_code}")

            # Оставляем комментарий (эта логика остается прежней)
            self.client.post("/comments/create/", json={
                "review": review_id,
                "text": "This is a test comment."
            }, name="/comments/create")


class SellerUser(AuthenticatedUser):
    """
    Поведение "Продавца".
    """
    wait_time = between(5, 15)  # Продавцы менее активны

    verify = False

    def on_start(self):
        """Настройка HTTP-клиента для игнорирования SSL-сертификатов"""
        self.client.verify = False
        super().on_start()

    @task(5)
    def manage_products(self):
        # Просматривает свои товары
        self.client.get("/products/list/?my_products=true", name="/products/list (my)")

    @task(1)
    def create_product(self):
        if CATEGORY_IDS:
            category_id = random.choice(CATEGORY_IDS)
            # Locust не умеет загружать файлы "из коробки", поэтому отправляем без картинки
            self.client.post("/products/create/", json={
                "title": f"New Test Product {random.randint(1000, 9999)}",
                "description": "Created by Locust load test.",
                "price": round(random.uniform(100.0, 5000.0), 2),
                "stock": random.randint(10, 100),
                "category": category_id,
            }, name="/products/create")
