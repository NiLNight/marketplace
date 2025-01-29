# Функциональные требования 🌟

## 1. 👨‍👦 Управление пользователями
### 1.1 🔐 Регистрация и аутентификация
**Требование:** Пользователи должны иметь возможность регистрироваться и аутентифицироваться  
**Описание:**  
- Регистрация через email/логин и пароль  
- Аутентификация по JWT-токенам (access/refresh)  
- Выход из системы через отзыв токенов  
**Модели:** `User`, `UserProfile`

### 1.2 📝 Профиль пользователя
**Требование:** Пользователи должны управлять персональными данными  
**Описание:**  
- Добавление/изменение номера телефона (с валидацией формата)  
- Загрузка аватара (JPG/PNG)  
- Указание даты рождения  
**Модели:** `UserProfile`

---

## 2. 🛍️ Управление каталогом товаров
### 2.1 🌳 Иерархия категорий
**Требование:** Администраторы должны управлять древовидной структурой категорий  
**Описание:**  
- Создание/редактирование вложенных категорий  
- Автогенерация SEO-дружественных URL (slug)  
**Модели:** `Category`

### 2.2 🧸 Работа с товарами
**Требование:** Администраторы должны управлять товарами  
**Описание:**  
- 🖼Добавление товаров с изображениями (JPG/PNG/WebP)  
- Установка цены, скидок и остатков на складе  
- Фильтрация по категориям и статусу (активен/скрыт)  
**Модели:** `Product`

---

## 3. 🛒 Корзина и заказы
### 3.1 🧺 Управление корзиной
**Требование:** Пользователи должны формировать корзину товаров  
**Описание:**  
- Добавление/удаление товаров в корзину  
- Работа с корзиной для гостей (по сессии) и авторизованных пользователей  
**Модели:** `OrderItem` (с `order = null`)

### 3.2 📦 Оформление заказов
**Требование:** Пользователи должны оформлять заказы  
**Описание:**  
- Преобразование корзины в заказ  
- Выбор адреса доставки и платежных реквизитов  
- Отслеживание статусов: `pending` → `processing` → `shipped`  
**Модели:** `Order`, `OrderItem`, `Delivery`, `Requisites`

---

## 4. ⭐ Отзывы и рейтинги
### 4.1 🌟 Система оценок
**Требование:** Пользователи могут оценивать товары  
**Описание:**  
- Оценка по 5-звездочной шкале  
- Защита от повторных оценок (1 оценка на пользователя)  
**Модели:** `Rating`

### 4.2 📝 Комментарии
**Требование:** Пользователи могут оставлять текстовые отзывы  
**Описание:**  
- Написание/редактирование комментариев к товарам  
- Привязка отзыва к оценке  
**Модели:** `Review`

---

## 5. 💰 Платежи и доставка
### 5.1 💳 Управление оплатой
**Требование:** Интеграция с платежными методами  
**Описание:**  
- Привязка платежных реквизитов  
- История транзакций со статусами (`completed`, `failed`)  
**Модели:** `Payment`, `Requisites`

### 5.2 🚚 Доставка
**Требование:** Управление адресами доставки  
**Описание:**  
- Добавление/редактирование адресов  
- Выбор адреса при оформлении заказа  
**Модели:** `Delivery`
