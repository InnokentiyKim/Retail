# 📚 Документация Online Market

## Содержание
- [Архитектура сервиса](#architecture)
- [Установка и настройка](#installation)
- [API документация](#api)
- [Работа с сервисом](#usage)

<a name="architecture"></a>
## 🏗️ Архитектура сервиса

### Схема архитектуры
<img src="../images/project_schema.png" alt="schema">

### Технологический стек

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Backend Framework | Django | 4.2+ |
| API | Django REST Framework | 3.15+ |
| Database | PostgreSQL | 15+ |
| Cache | Redis | 7.0+ |
| Task Queue | Celery | 5.3+ |
| Message Broker | RabbitMQ | 3.11+ |
| Containerization | Docker & Docker Compose | 24.0+ |

### Компоненты системы

#### 1. Web-сервер (Django)
- Обработка HTTP-запросов
- REST API endpoints
- Аутентификация и авторизация через JWT
- Административная панель

#### 2. База данных (PostgreSQL)
- Хранение данных пользователей
- Каталог товаров и заказов
- Информация о магазинах и продавцах

#### 3. Кэш (Redis)
- Кэширование часто запрашиваемых данных
- Хранение сессий
- Оптимизация производительности

#### 4. Очередь задач (Celery + RabbitMQ)
- Асинхронная отправка email-уведомлений
- Генерация PDF-отчетов
- Фоновая обработка импорта товаров

---

<a name="installation"></a>
## 🚀 Установка и настройка

### Предварительные требования

- Docker версии 24.0+
- Docker Compose версии 2.20+
- Git

### Быстрый старт

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd Retail
```

2. **Настройка переменных окружения**

Создайте файл `.env` в корне проекта:

```bash
# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=retail_db
DB_USER=postgresql
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis Cache
REDIS_CACHE_HOST=redis-cache
REDIS_CACHE_PORT=6379
REDIS_CACHE_DB=0

# Redis Database
REDIS_HOST=redis-db
REDIS_PORT=6379
REDIS_DB=0

# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (Gmail example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Celery
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672/
CELERY_RESULT_BACKEND=redis://redis-db:6379/1
```

3. **Запуск с помощью Docker Compose**

```bash
docker-compose up -d
```

4. **Применение миграций**

```bash
docker-compose exec web python manage.py migrate
```

5. **Создание суперпользователя**

```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Сервис доступен по адресу**
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- Swagger: http://localhost:8000/api/docs/

### Ручная установка (без Docker)

1. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

2. **Запуск необходимых сервисов**
```bash
# PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15

# Redis (cache)
docker run -d -p 6379:6379 redis:7

# Redis (database)
docker run -d -p 6380:6379 redis:7

# RabbitMQ
docker run -d -p 5672:5672 rabbitmq:3.11
```

3. **Обновите переменные окружения**
```bash
DB_HOST=localhost
REDIS_CACHE_HOST=localhost
REDIS_HOST=localhost
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672/
```

4. **Применение миграций и запуск**
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

5. **Запуск Celery worker**
```bash
celery -A retail worker -l info
```

---

<a name="api"></a>
## 📖 API документация

### Базовый URL
```
http://localhost:8000/api/v1/
```

### Аутентификация

Сервис использует JWT (JSON Web Token) для аутентификации.

**Получение токена:**
```http
POST /api/v1/user/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Использование токена:**
```http
GET /api/v1/user/account
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Основные endpoints

#### 🔐 Пользователи

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/user/register` | Регистрация нового пользователя |
| POST | `/user/register/confirm` | Подтверждение email |
| POST | `/user/login` | Вход в систему |
| POST | `/user/login/refresh` | Обновление токена |
| GET | `/user/account` | Информация об аккаунте |
| POST | `/user/account` | Обновление аккаунта |
| POST | `/user/password_reset` | Сброс пароля |
| POST | `/user/password_reset/confirm` | Подтверждение сброса пароля |

#### 📦 Товары

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/products/products` | Каталог товаров |
| GET | `/products/categories` | Категории товаров |
| GET | `/products/shops` | Список магазинов |
| GET | `/products/popular` | Популярные товары |

#### 🛒 Покупатель

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET/POST/PUT/DELETE | `/buyer/shoppingcart` | Управление корзиной |
| GET/POST | `/buyer/orders` | Заказы покупателя |

#### 🏪 Продавец

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/seller/shop` | Создание магазина |
| GET/POST | `/seller/status` | Статус магазина |
| POST | `/seller/goods` | Импорт товаров |
| GET | `/seller/products` | Товары магазина |
| GET | `/seller/orders` | Заказы магазина |

#### 👨‍💼 Менеджер

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET/POST | `/manager/orders` | Управление заказами |
| GET/POST/PUT/DELETE | `/manager/coupons` | Управление купонами |

### Swagger документация

Полная интерактивная документация API доступна по адресу:
```
http://localhost:8000/api/docs/
```

---

<a name="usage"></a>
## 💡 Работа с сервисом

### Роли пользователей

#### 👤 Покупатель (Buyer)
- Просмотр каталога товаров
- Поиск и фильтрация товаров
- Добавление товаров в корзину
- Оформление заказов
- Отслеживание статуса заказов
- Применение скидочных купонов

#### 🏪 Продавец (Seller)
- Создание и управление магазином
- Импорт каталога товаров из YAML
- Управление статусом магазина
- Просмотр заказов своих товаров
- Мониторинг продаж

#### 👨‍💼 Менеджер (Manager/Admin)
- Управление всеми заказами
- Изменение статусов заказов
- Создание и управление скидочными купонами
- Доступ к административной панели
- Экспорт данных в CSV

### Примеры использования

#### Регистрация пользователя

```bash
curl -X POST http://localhost:8000/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer@example.com",
    "password": "SecurePass123!",
    "username": "buyer_user",
    "first_name": "John",
    "last_name": "Doe",
    "type": "BR"
  }'
```

#### Получение каталога товаров

```bash
curl -X GET "http://localhost:8000/api/v1/products/products?category_id=1&ordering=price" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Добавление товара в корзину

```bash
curl -X POST http://localhost:8000/api/v1/buyer/shoppingcart \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_item": 5,
    "quantity": 2
  }'
```

#### Подтверждение заказа

```bash
curl -X POST http://localhost:8000/api/v1/buyer/orders \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "contact": 1,
    "coupon_code": "DISCOUNT10"
  }'
```

#### Импорт товаров (продавец)

```bash
curl -X POST http://localhost:8000/api/v1/seller/goods \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/shop_catalog.yaml"
  }'
```

### Формат файла импорта товаров (YAML)

```yaml
shop: "Название магазина"
categories:
  - id: 1
    name: "Электроника"
  - id: 2
    name: "Одежда"

goods:
  - id: 1
    category: 1
    name: "Смартфон Samsung Galaxy"
    model: "S21"
    price: 45000
    price_rrc: 50000
    quantity: 10
    parameters:
      color: "Черный"
      memory: "128GB"
  
  - id: 2
    category: 2
    name: "Футболка"
    model: "Classic"
    price: 1500
    price_rrc: 2000
    quantity: 50
    parameters:
      size: "L"
      material: "Хлопок"
```

### Административная панель

Доступна по адресу: http://localhost:8000/admin/

**Возможности:**
- Управление пользователями
- Просмотр и редактирование заказов
- Управление товарами и магазинами
- Создание купонов
- Экспорт данных в CSV
- Статистика и аналитика

### Email-уведомления

Пользователи получают уведомления при:
- Регистрации (подтверждение email)
- Сбросе пароля
- Создании заказа (с PDF-отчетом)
- Изменении статуса заказа

### Фильтры и сортировка

#### Товары
```
GET /api/v1/products/products?category_id=1&shop_id=2&search=phone&ordering=price
```

#### Категории
```
GET /api/v1/products/categories?search=electronics&ordering=name
```

#### Магазины
```
GET /api/v1/products/shops?id=1&search=market&ordering=name
```

### Пагинация

Все списковые endpoints поддерживают пагинацию:
```
GET /api/v1/products/products?page=2&page_size=20
```

### Throttling (ограничение запросов)

- Анонимные пользователи: 100 запросов/час
- Авторизованные пользователи: 1000 запросов/час

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=backend --cov-report=html

# Конкретный модуль
pytest tests/backend/test_api.py
```

---

## 🔧 Разработка

### Структура проекта

```
RetailProject/
├── backend/              # Основное приложение
│   ├── models.py        # Модели данных
│   ├── views.py         # Представления API
│   ├── serializers.py   # Сериализаторы
│   ├── urls.py          # URL-маршруты
│   ├── tasks.py         # Celery задачи
│   └── signals.py       # Django сигналы
├── retail/              # Настройки проекта
│   ├── settings.py      # Конфигурация
│   ├── urls.py          # Корневые URL
│   └── celery.py        # Настройки Celery
├── tests/               # Тесты
├── templates/           # HTML-шаблоны
├── data/                # Данные для импорта
├── docker-compose.yml   # Docker конфигурация
├── requirements.txt     # Python зависимости
└── manage.py            # Django CLI
```

### Полезные команды

```bash
# Создание миграций
docker-compose exec web python manage.py makemigrations

# Применение миграций
docker-compose exec web python manage.py migrate

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser

# Сбор статических файлов
docker-compose exec web python manage.py collectstatic

# Запуск shell
docker-compose exec web python manage.py shell

# Просмотр логов
docker-compose logs -f web

# Перезапуск сервисов
docker-compose restart

# Остановка и удаление контейнеров
docker-compose down
```

---

## 📊 Мониторинг и логирование

### Логи приложения

```bash
# Все логи
docker-compose logs

# Логи конкретного сервиса
docker-compose logs web
docker-compose logs celery
docker-compose logs rabbitmq

# Следить за логами в реальном времени
docker-compose logs -f web
```

### Мониторинг Celery

```bash
# Статус worker'ов
docker-compose exec celery celery -A retail inspect active

# Список зарегистрированных задач
docker-compose exec celery celery -A retail inspect registered
```

---

## 🐛 Troubleshooting

### Проблемы с подключением к БД

```bash
# Проверка статуса контейнера
docker-compose ps db

# Перезапуск БД
docker-compose restart db

# Логи БД
docker-compose logs db
```

### Проблемы с Celery

```bash
# Проверка RabbitMQ
docker-compose logs rabbitmq

# Перезапуск Celery worker
docker-compose restart celery
```

### Сброс базы данных

```bash
# Остановка контейнеров
docker-compose down

# Удаление volumes
docker-compose down -v

# Пересоздание
docker-compose up -d
docker-compose exec web python manage.py migrate
```

---

## 👨‍💻 Автор

[InnCent](https://github.com/InnokentiyKim/)

