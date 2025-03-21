
[<img src="./images/Market.jpg" width="240" height="240">](https://github.com/InnokentiyKim/LearnEnglishTgBot/)
[![Coverage](https://img.shields.io/badge/Coverage-$(echo ${{ github.event.pull_request.labels }} | grep -oP '(?<=coverage=).*?(?=%)')-%23green)](https://github.com/InnokentiyKim/Retail/actions/workflows/coverage.yml)

# Online Market – это REST API сервис для продажи и покупки разнообразных товаров.
> #### Сервис позволяет покупателям находить нужные товары, делать заказы, управлять ими, следить за их статусом и получать уведомления об изменениях
> #### Сервис позволяет продавцам создавать каталог товаров, управлять своим магазином, следить за продажами и заказами
> #### Маркет предоставляет менеджерам удобные инструменты для управления и мониторинга системами продаж
### Функционал сервиса позволяет:
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">пользователям регистрироваться и аутентифицироваться в сервисе с помощью jwt токена, выполнять сброс пароля</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">просматривать каталог и категории товаров, выполнять поиск товаров, применять различные фильтры и сортировку</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">добавлять товары в корзину, подтверждать заказы, применять скидочные купоны к заказам</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">получать уведомления на email о статусе заказа с прикреплением отчета о созданном заказе в формате pdf</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">для продавцов создавать и управлять магазинами, выполнять загрузку и обновление каталога товаров</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">для менеджеров предоставляется удобная адмнистративная панель для мониторинга и управления пользователями, магазинами и заказами, с возможностью выгружать данные в формате csv</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">для улучшения работы сервиса применяется пагинация и механизм тротлинга, кэширование и асинхронное выполнение ресурсоемких задач</span>
> - <span style="color: #FFFF00; text-shadow: 1px 1px 1px #000000">для тестирования и проверки работы сервиса предоставляется документация в формате swagger</span>
### Технологии и инструменты
> - Django <img src="images/django-logo.svg" alt="Django" width="20" height="20">
> - PostgreSQL <img src="images/postgresql-logo.svg" alt="Postgresql" width="20" height="20">
> - Redis <img src="images/redis-logo.svg" alt="Redis" width="20" height="20">
> - Celery <img src="images/celery-logo.svg" alt="Celery" width="20" height="20">
> - RabbitMQ <img src="images/rabbitmq-logo.svg" alt="RabbitMQ" width="20" height="20">
> - Docker <img src="images/docker-logo.svg" alt="Docker" width="20" height="20">
> - Docker Compose <img src="images/compose-logo.svg" alt="Docker-Compose" width="20" height="20">
### Схема архитектуры сервиса
<img src="images/project_schema.png" alt="schema">
<hr>

- [Начало работы](#start)
  - [Настройка и запуск проекта](#environment)
  - [Переменные окружения](#variables)
  - [Зависимости](#dependencies)
- [Работа сервиса](#service)
  - [Пользователь](#user)
    - [Регистрация и аутентификация пользователя](#registration)
    - [Управление аккаунтом и контактами](#account_contacts)
    - [Получение каталога (категорий) товаров, списка магазинов и популярных товаров](#products)
  - [Покупатель](#buyer) 
    - [Работа с корзиной](#cart)
    - [Подтверждение и мониторинг статуса заказа](#order)
  - [Продавец](#seller)
    - [Создание магазина, получение и изменение статуса](#shop)
    - [Импорт товаров и обновление каталога](#goods)
    - [Получение заказов и активного каталога своих товаров](#shop_management)
  - [Менеджер](#manager)
    - [Мониторинг и управление заказами](#monitoring) 
    - [Получение и управление скидочными купонами](#coupons) 
    - [Работа с сайтом администрирования](#panel) 
- [Документация](#docs)

<a name="start"></a>
## 1. Начало работы

Запустить проект рекомендуется в Docker, однако возможно запустить его и вручную.
_Все необходимые действия и данные для работы сервиса описаны ниже._

<a name="environment"></a>
### 1.1. Настройка и запуск проекта

Для запуска проекта необходимо настроить переменные окружения (.env файл) и выполнить команду `docker-compose up`.

<a name="variables"></a>
### 1.2. Переменные окружения
Всю чувствительную информацию, необходимую для работы сервиса, рекомендуется хранить в файле (.env) в корне проекта.   
_Список переменных окружения (по умолчанию/рекомендуемые):_   
- Настройка основной базы данных PostgreSQL:
   >- _DB_ENGINE - движок базы данных (django.db.backends.postgresql)_.
   >- _DB_NAME - имя базы данных (retail_db)_
   >- _DB_USER - имя пользователя для подключения к БД (postgresql)_  
   >- _DB_PASSWORD - пароль пользователя для подключения к БД (postgres)_
   >- _DB_HOST - имя хоста (db)_
   >- _DB_PORT - номер порта (5432)_.    
- Настройка Redis для кэша:     
   >- _REDIS_CACHE_HOST - имя хоста (redis-cache)_
   >- _REDIS_CACHE_PORT - номер порта (6379)_
   >- _REDIS_CACHE_DB - номер базы (0)_.   
- Настройка Redis базы данных:    
   >- _REDIS_HOST - имя хоста (redis-db)_
   >- _REDIS_PORT - номер порта (6379)_
   >- _REDIS_DB - номер базы (0)_.   
- Настройка приложения Django:  
   >- _DEBUG - отключение режима отладки (False)_
   >- _EMAIL_BACKEND - настройка почтового сервиса (django.core.mail.backends.smtp.EmailBackend)_
   >- _EMAIL_HOST - хост почтового сервиса (smtp.gmail.com)_
   >- _EMAIL_HOST_USER - имя пользователя почтового сервиса (innokentiykim90@gmail.com)_
   >- _EMAIL_HOST_PASSWORD - пароль от почтового сервиса (пароль приложения)_
   >- _EMAIL_PORT - порт почтового сервиса (587)_.   
- Настройка Celery:   
   >- _CELERY_BROKER_URL - настройка брокера сообщений (amqp://guest:guest@rabbitmq:5672/)_
   >- _CELERY_RESULT_BACKEND - настройка бэкенда (redis://redis-db:6379/1)_

<a name="dependencies"></a>
### 1.3. Зависимости

В случае ручного запуска проекта сначала необходимо установить все зависимости. (_используйте файл `requirements.txt` в корне проекта: `pip install -r requirements.txt`_).  
* Последовательность действий:   
  - Последовательно запустите все необходимые для работы сервисы (`db`, `rabbitmq`, `redis-cache`, `redis-db`), можно в докер-контейнере: `docker-compose up <название сервиса>`.  
  - Примените миграции: `python manage.py migrate`.  
  - Запустите приложение Django: `python manage.py runserver 0.0.0.0:8000`.  
* В этом случае необходимо добавить только переменные окружения самого приложения (см. Настройка приложения Django), остальные уже установлены по-умолчанию

<a name="service"></a>
## 2. Работа сервиса

<a name="user"></a>
### 2.1. Пользователь
Пользователь может зарегистрироваться и входить в систему с помощью email и пароля.

<a name="registration"></a>
#### 2.1.1. Регистрация и аутентификация пользователя
* Создание аккаунта `POST /api/v1/user/register`. Тело запроса:    
  - `email` - email пользователя (cтрока)
  - `password` - пароль пользователя (cтрока)
  - `username` - имя пользователя (cтрока)
  - `first_name` - имя пользователя (cтрока)
  - `last_name` - фамилия пользователя (cтрока)
  - `type` - тип пользователя (возможные значения: 'BR' - покупатель, 'SL' - продавец (по умолчанию 'BR')).  
* После необходимо с помощью полученного на почту токена подтвердить свой email для активации аккаунта.    
Для этого необходимо отправить запрос `POST /api/v1/user/register/confirm`. Тело запроса: 
  - `email` - email пользователя (cтрока)
  - `token` - токен полученный на почту (cтрока)
* После успешного подтверждения пользователь может логиниться в системе.   
При успехе пользователь получает JWT токен (пара значений: access-токен доступа и refresh-токен обновления).
Чтобы залогиниться необходимо отправить запрос `POST /api/v1/user/login`. Тело запроса:    
  - `email` - email пользователя (cтрока)
  - `password` - пароль пользователя (cтрока)
* Для обновления пары токенов необходимо отправить запрос с имеющимся refresh-токеном `POST /api/v1/user/login/refresh`. Тело запроса:    
  - `refresh` - refresh-токен (cтрока)
* Чтобы сбросить свой пароль от аккаунта необходимо отправить запрос `POST /api/v1/user/password_reset`. Тело запроса:    
  - `email` - email пользователя (cтрока)
На почту пользователя будет отправлен токен для подтверждения сброса пароля.
Для подтверждения необходимо отправить запрос `POST /api/v1/user/password_reset/confirm`. Тело запроса:   
  - `password` - новый пароль пользователя (cтрока)
  - `token` - токен полученный на почту (cтрока)


<a name="account_contacts"></a>
#### 2.1.2. Управление аккаунтом и контактами
Пользователь может получить и изменить информацию об аккаунте, создавать контакты (необходимы для подтверждения заказа покупателем) и управлять ими.   
Любому пользователю доступны следующие действия:    
* Получить информацию об аккаунте `GET /api/v1/user/account`.       
* Изменение информации об аккаунте `POST /api/v1/user/account`. Тело запроса (возможные поля):    
  - `email` - email пользователя (cтрока)
  - `password` - пароль пользователя (cтрока)
  - `username` - имя пользователя (cтрока)
  - `first_name` - имя пользователя (cтрока)
  - `last_name` - фамилия пользователя (cтрока)
  - `type` - тип пользователя (возможные значения: 'BR' - покупатель, 'SL' - продавец (по умолчанию 'BR')).
* Создание контакта `POST /api/v1/user/contact`. Тело запроса (возможные поля):    
  - `phone` - номер телефона (cтрока)
  - `country` - страна (cтрока - опционально)
  - `city` - город (cтрока)
  - `street` - улица (cтрока)
  - `house` - дом (cтрока)
  - `apartment` - квартира (cтрока)
  - `structure` - корпус (cтрока - опционально)
  - `building` - здание (cтрока - опционально)
* Получение информации о контактах `GET /api/v1/user/сontact`.       
* Изменение контакта `PUT /api/v1/user/contact`. Тело запроса (возможные поля):    
  - `id` - id контакта (целое число)
  - `<parameter>` - изменяемый параметр
* Удаление контакта(ов) `DELETE /api/v1/user/contact`. Тело запроса:    
  - `items` - список id контактов для удаления (список целых чисел)

<a name="products"></a>
#### 2.1.3. Получение каталога (категорий) товаров, списка магазинов и популярных товаров
Пользователи могут просматривать каталог и категории товаров, магазины и популярные товары.     
При этом также доступны фильтры, передаваемые через query-параметры запроса.   
Любому пользователю доступны следующие действия:    
* Получение каталога товаров `GET /api/v1/products/products`. Доступные фильтры:    
  - фильтр по категории товара - `category_id`
  - фильтр по id магазина - `shop_id`
  - поисковый фильтр по названию - `search`
  - сортировка результатов по `id` или `price` (цене) товара - `ordering`
* Получение категорий товаров `GET /api/v1/products/categories`. Доступные фильтры:    
  - фильтр по id категории - `id`
  - поисковый фильтр по названию - `search`
  - сортировка результатов по `id` или `name` (названию) - `ordering`
* Получение списка магазинов `GET /api/v1/products/shops`. Доступные фильтры:    
  - фильтр по id магазина - `id`
  - поисковый фильтр по названию - `search`
  - сортировка результатов по `id` или `name` (названию) - `ordering`
* Получение популярных товаров `GET /api/v1/products/popular`. Доступные параметры:    
  - количество популярных товаров (по умолчанию 5) - `amount`



<a name="buyer"></a>
### 2.2. Покупатель
Для покупателя доступны поиск и просмотр товаров, добавление товаров в корзину, изменение корзины товаров, подтверждение заказа, просмотр активного заказа и истории заказов.

<a name="cart"></a>
#### 2.2.1. Работа с корзиной
<u>_Представления доступны только для аутентифицированных покупателей._</u>     
После того как пользователь нашел интересующий его товар, он может добавить его в корзину.
* Запрос для добавления товара в корзину (создание корзины) `POST /api/v1/buyer/shoppingcart`. Тело запроса:    
  - `product_item` - id товара (целое число)
  - `quantity` - количество товара (целое число)
* Для просмотра активной корзины `GET /api/v1/buyer/shoppingcart`.
* Чтобы изменить количество товара в корзину `PUT /api/v1/buyer/shoppingcart`. Тело запроса:    
  - `id` - id товара (целое число)
  - `quantity` - количество товара (целое число)
* Для удаления товара(ов) в корзине необходимо передать список id товаров `DELETE /api/v1/buyer/shoppingcart`. Тело запроса:    
  - `items` - список id товара(ов) (список целых чисел)

<a name="order"></a>
#### 2.2.2. Подтверждение и мониторинг статуса заказа
<u>_Представления доступны только для аутентифицированных покупателей._</u>     
После того как пользователь собрал корзину товаров для покупки, он должен подтвердить заказ.   
Для этого в теле запроса нужно передать id корзины, активный контакт пользователя и номер купона (опционально).
* Запрос для подтверждения заказа `POST /api/v1/buyer/orders`. Тело запроса:    
  - `id` - id корзины (целое число)
  - `contact` - id активного контакта пользователя (целое число)
  - `coupon_code` - код скидочного купона (cтрока - опционально)
* Для просмотра состояния активного заказа и истории всех заказов нужно отправить `GET /api/v1/buyer/orders`.


<a name="seller"></a>
### 2.3. Продавец

<a name="shop"></a>
#### 2.3.1. Создание магазина, получение и изменение статуса
<u>_Представления доступны только для аутентифицированных продавцов._</u>     
* Для импорта товаров и обновление каталога необходимо послать запрос `POST /api/v1/seller/shop`. Тело запроса:    
  - `name` - название магазина (cтрока)
  - `url` - url-адрес веб-сайта магазина (cтрока - опционально)
  - `description` - url-адрес магазина (cтрока - опционально)
  - `is_active` - статус магазина (Булево значение - по умолчанию False)
* Для получения текущего статуса магазина необходимо послать запрос `GET /api/v1/seller/status`.      
* Для изменения текущего статуса магазина необходимо послать запрос `POST /api/v1/seller/status`. Тело запроса:
  - `is_active` - статус магазина (Булево значение)

<a name="import"></a>
#### 2.3.2. Импорт товаров и обновление каталога
<u>_Представления доступны только для аутентифицированных продавцов._</u>
* Для создания магазина необходимо послать запрос `POST /api/v1/seller/goods`. Тело запроса:    
  - `url` - url-адрес файла в формате yaml для импорта товаров (cтрока)

<a name="shop_management"></a>
#### 2.3.3. Получение заказов и активного каталога своих товаров
<u>_Представления доступны только для аутентифицированных продавцов._</u>     
* Запрос на получение активного каталога товаров `GET /api/v1/seller/products`.
* Запрос на получение списка заказов `GET /api/v1/seller/orders`


<a name="manager"></a>
### 2.4. Менеджер

<a name="monitoring"></a>
#### 2.4.1. Мониторинг и управление заказами 
<u>_Представления доступны только для аутентифицированных администраторов._</u>     
Работа с заказами подразумевает следующие действия:    
* Обновление статуса заказа по запросу `POST /api/v1/manager/orders`. Тело запроса:    
  - `id` - id заказа (целое число)
  - `state` - новый статус заказа (возможные значения: `CREATED, CONFIRMED, ASSEMBLED, SENT, DELIVERED, CANCELED`)
* Получение списка заказов по запросу `GET /api/v1/manager/orders`

<a name="coupons"></a>
#### 2.4.2. Получение и управление скидочными купонами 
<u>_Представления доступны только для аутентифицированных администраторов._</u>     
Работа со скидочными купонами подразумевает следующие действия:    
* Создание скидочного купона по запросу `POST /api/v1/manager/coupons`. Тело запроса:    
  - `code` - код купона (строка)
  - `valid_from` - дата начала действия купона (необязательно - дата в формате ISO)
  - `valid_to` - дата окончания действия купона (необязательно (по умолчанию 30 дней) - дата в формате ISO)
  - `discount` - процент скидки (число в диапазоне от 0 до 100)
  - `active` - процент скидки (необязательно (по умолчанию True) - логическая переменная)
* Получение скидочных купонов по запросу `GET /api/v1/manager/coupons`
* Изменение скидочного купона по запросу `PUT /api/v1/manager/coupons`. Тело запроса:    
  - `id` - id купона (целое число)
  - `<изменяемые(ое) поля>`
* Удаление скидочного купона по запросу `DELETE /api/v1/manager/coupons`. Тело запроса:    
  - `items` - список id купона(ов) (список целых чисел)

<a name="panel"></a>
#### 2.4.3. Работа с сайтом администрирования
Сайт администрирования доступен для администраторов (менеджеров) по адресу http://127.0.0.1:8000/admin/.  
Сайт администрирования предоставляет удобные инструменты и позволяет выполнять следующие действия:
* Просмотр и редактирование информации о пользователях, покупателях и продавцах (магазинах)
* Просмотр и редактирование информации о товарах, заказах и купонах
* Изменение статуса заказа
* Выгрузка любых выбранных данных в формате CSV


<a name="docs"></a>
## 3. Документация

Документация по проекту доступна в формате Swagger: [localhost:8000/api/docs](http://127.0.0.1:8000/api/docs/).  
**Заметка: Метод DELETE OpenAPI не поддерживает передачу тела запроса*


---
Автор:
[InnCent](https://github.com/InnokentiyKim/)
