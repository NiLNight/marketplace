# Функциональные требования

## 1. 👨‍👦 Управление пользователями

### 1.1 🔐 Регистрация и аутентификация
**Требования:**
- Пользователи должны иметь возможность регистрироваться, аутентифицироваться и выходить из аккаунта.
- Регистрация через email/логин и пароль с подтверждением email (отправка ссылки для верификации).
- Аутентификация по JWT-токенам (access/refresh).
- *Поддержка возможности включения двухфакторной аутентификации (2FA) для повышения безопасности.
- Выход из системы осуществляется посредством отзыва токенов.
- *Интеграция с социальными сетями для альтернативной аутентификации.

**Модели:** `User`, `UserProfile`

### 1.2 📝 Профиль пользователя
**Требования:**
- Пользователи должны иметь возможность управлять своими персональными данными.
- Добавление и изменение данных профиля.
- Просмотр информации профиля.
- Смена пароля и почты аккаунта с подтверждением новых данных.

**Модели:** `UserProfile`

---

## 2. 🛍️ Управление каталогом товаров

### 2.1 🌳 Иерархия категорий
**Требования:**
- Администраторы должны иметь возможность управлять древовидной структурой категорий.
- Создание и редактирование вложенных категорий.
- Автогенерация SEO-дружественных URL (slug).
- Использование кэширования Redis для ускорения выборки категорий.

**Модели:** `Category`

### 2.2 🧸 Работа с товарами
**Требования:**
- Пользователи должны иметь возможность управлять товарами.
- Добавление товаров с изображениями.
- Установка цены, скидок и остатков на складе.
- Фильтрация товаров по категориям и статусу (активен/скрыт) с возможностью сортировки и полнотекстового поиска.
- Использование кэширования для часто запрашиваемых данных.

**Модели:** `Product`

---

## 3. 🛒 Корзина и заказы

### 3.1 🧺 Управление корзиной
**Требования:**
- Пользователи должны иметь возможность формировать и управлять корзиной товаров.
- Добавление и удаление товаров из корзины.
- Корзина для авторизованных пользователей хранится в базе данных, а для гостей — реализована на основе сессии.

**Модели:** `OrderItem` (с `order = null` для временного хранения)

### 3.2 📦 Оформление заказов
**Требования:**
- Пользователи должны иметь возможность оформлять заказы, преобразуя корзину в заказ.
- Выбор адреса доставки и платежных реквизитов при оформлении заказа.
- Отслеживание статусов заказа: `pending` → `processing` → `shipped` с возможностью расширения (например, «отменен», «доставлен», «возврат»).
- *Уведомления пользователей о смене статуса заказа.
- Возможность просмотра истории заказов.

**Модели:** `Order`, `OrderItem`, `Delivery`, `Requisites`

---

## 4. ⭐ Отзывы и рейтинги

### 4.1 🌟 Система оценок
**Требования:**
- Пользователи могут оценивать товары по 5-звездочной шкале.
- Защита от повторных оценок — один пользователь может оставить только одну оценку.

**Модели:** `Rating`

### 4.2 📝 Комментарии
**Требования:**
- Пользователи могут оставлять текстовые отзывы к товарам.
- Возможность создания, редактирования и удаления комментариев.
- Привязка отзыва к соответствующей оценке.

**Модели:** `Review`

---

## 5. 💰 Платежи и доставка

### 5.1 💳 Управление оплатой
**Требования:**
- *Интеграция с платежными системами для проведения транзакций.
- Привязка платежных реквизитов к аккаунту пользователя.
- Хранение истории транзакций с указанием статусов (`completed`, `failed` и др.).
- *Обработка ошибок платежей, возврат средств и логирование операций для аудита.

**Модели:** `Payment`, `Requisites`

### 5.2 🚚 Доставка
**Требования:**
- Пользователи должны иметь возможность управлять адресами доставки.
- Добавление и редактирование адресов доставки.
- Выбор адреса доставки при оформлении заказа.
- *Интеграция с внешними сервисами доставки для отслеживания статуса заказа.

**Модели:** `Delivery`

