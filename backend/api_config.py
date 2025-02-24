from drf_spectacular.utils import extend_schema_field, OpenApiResponse
from backend.serializers import CategorySerializer, OrderSerializer, OrderConfirmSerializer, \
    OrderItemCreateUpdateSerializer, OrderItemSerializer, OrderItemUpdateSerializer, OrderItemDeleteSerializer, \
    CouponSerializer, ObjectIDSerializer, OrderStateSerializer, ProductItemSerializer, ProductSerializer, \
    ShopSerializer, UserSerializer, ContactSerializer
from rest_framework import status


class APIConfig:

    @staticmethod
    def get_category_config():
        return {
            "description": "Получить список категорий товаров",
            "summary": "Получить список категорий товаров",
            "tags": ["Товары"],
            "operation_id": "get_category",
            "deprecated": False,
            "filters": True,
            "parameters": [
                {
                    "name": "filter",
                    "in": "query",
                    "description": "Фильтр по id или названию",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "search",
                    "in": "query",
                    "description": "Поиск по названию",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "ordering",
                    "in": "query",
                    "description": "Сортировка по id или названию",
                    "required": False,
                    "type": "string"
                }
            ],
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=CategorySerializer, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def get_buyer_orders():
        return {
            "description": "Получить историю заказов покупателя",
            "summary": "Получить историю заказов покупателя",
            "tags": ["Покупатель"],
            "operation_id": "get_buyer_orders",
            "deprecated": False,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=OrderSerializer, description="OK"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def confirm_buyer_order_config():
        return {
            "description": "Подтверждение заказа покупателя",
            "summary": "Подтверждение заказа покупателя",
            "tags": ["Покупатель"],
            "operation_id": "confirm_buyer_order",
            "deprecated": False,
            "request": OrderConfirmSerializer,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=OrderConfirmSerializer, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Order already confirmed")
                }
        }

    @staticmethod
    def get_shopping_cart_config():
        return {
            "description": "Получить список товаров в корзине",
            "summary": "Получить список товаров в корзине",
            "tags": ["Покупатель"],
            "operation_id": "get_shopping_cart",
            "deprecated": False,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=OrderSerializer, description="OK"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found"),
                }
        }

    @staticmethod
    def create_shopping_cart_config():
        return {
            "description": "Создание/обновление корзины покупателя",
            "summary": "Создание/обновление корзины покупателя",
            "tags": ["Покупатель"],
            "operation_id": "create_shopping_cart",
            "deprecated": False,
            "request": OrderItemCreateUpdateSerializer(many=True),
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
                }
        }

    @staticmethod
    def update_shopping_cart_config():
        return {
            "description": "Изменение количества товаров в корзине покупателя",
            "summary": "Изменение количества товаров в корзине покупателя",
            "tags": ["Покупатель"],
            "operation_id": "update_shopping_cart",
            "deprecated": False,
            "request": OrderItemUpdateSerializer(many=True),
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
                }
        }

    @staticmethod
    def delete_shopping_cart_config():
        return {
            "description": "Удаление товаров из корзины покупателя",
            "summary": "Удаление товаров из корзины покупателя",
            "tags": ["Покупатель"],
            "operation_id": "update_shopping_cart",
            "deprecated": False,
            "request": OrderItemDeleteSerializer(many=True),
            "responses":
                {
                    status.HTTP_204_NO_CONTENT: OpenApiResponse(response={}, description="No content"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
                }
        }

    @staticmethod
    def get_coupons_config():
        return {
            "description": "Получить список скидочных купонов",
            "summary": "Получить список скидочных купонов",
            "tags": ["Менеджер"],
            "operation_id": "get_coupons",
            "deprecated": False,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=CouponSerializer, description="OK"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized")
                }
        }

    @staticmethod
    def create_coupon_config():
        return {
            "description": "Создание скидочного купона",
            "summary": "Создание скидочного купона",
            "tags": ["Менеджер"],
            "operation_id": "create_coupon",
            "deprecated": False,
            "request": CouponSerializer,
            "responses":
                {
                    status.HTTP_201_CREATED: OpenApiResponse(response={}, description="Created"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
                }
        }

    @staticmethod
    def update_coupon_config():
        return {
            "description": "Обновление скидочного купона",
            "summary": "Обновление скидочного купона",
            "tags": ["Менеджер"],
            "operation_id": "update_coupon",
            "deprecated": False,
            "request": CouponSerializer,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def delete_coupon_config():
        return {
            "description": "Удаление скидочного купона",
            "summary": "Удаление скидочного купона",
            "tags": ["Менеджер"],
            "operation_id": "delete_coupon",
            "deprecated": False,
            "request": ObjectIDSerializer,
            "responses":
                {
                    status.HTTP_204_NO_CONTENT: OpenApiResponse(response={}, description="No content"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
                }
        }

    @staticmethod
    def get_manager_orders_config():
        return {
            "description": "Получить список заказов",
            "summary": "Получить список заказов",
            "tags": ["Менеджер"],
            "operation_id": "get_manager_orders",
            "deprecated": False,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=OrderSerializer, description="OK"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def update_manager_order_config():
        return {
            "description": "Обновление статуса заказа",
            "summary": "Обновление статуса заказа",
            "tags": ["Менеджер"],
            "operation_id": "update_manager_order",
            "deprecated": False,
            "request": OrderStateSerializer,
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def get_products_config():
        return {
            "description": "Получить список всех товаров",
            "summary": "Получить список всех товаров",
            "tags": ["Товары"],
            "operation_id": "get_products",
            "deprecated": False,
            "filters": True,
            "parameters": [
                {
                    "name": "filter",
                    "in": "query",
                    "description": "Фильтр по id магазина или категории товаров",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "search",
                    "in": "query",
                    "description": "Поиск по названию",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "ordering",
                    "in": "query",
                    "description": "Сортировка по id, названию товара, магазина или цене",
                    "required": False,
                    "type": "string"
                }
            ],
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=ProductItemSerializer, description="OK"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def get_popular_products_config():
        return {
            "description": "Получить список наиболее популярных товаров",
            "summary": "Получить список наиболее популярных товаров",
            "tags": ["Товары"],
            "operation_id": "get_popular_products",
            "deprecated": False,
            "parameters": [
                {
                    "name": "amount",
                    "in": "query",
                    "description": "Количество популярных товаров",
                    "required": False,
                    "type": "integer"
                },
            ],
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response=ProductSerializer(many=True), description="OK"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
                }
        }

    @staticmethod
    def import_seller_goods_config():
        return {
            "description": "Импорт товаров магазина",
            "summary": "Импорт товаров магазина",
            "tags": ["Продавец"],
            "operation_id": "import_seller_products",
            "deprecated": False,
            "request": {
                "required": True,
                "description": "Ссылка на YAML-файл",
                "schema": {
                    "type": "string",
                    "format": "url",
                    "description": "Ссылка на YAML-файл",
                    "example": "https://example.com/products.yaml"
                }
            },
            "responses":
                {
                    status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                    status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                    status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found"),
                    status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
                }
        }

    @staticmethod
    def get_seller_orders_config():
        return {
            "description": "Получить список заказов продавца",
            "summary": "Получить список заказов продавца",
            "tags": ["Продавец"],
            "operation_id": "get_seller_orders",
            "deprecated": False,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response=OrderSerializer(many=True), description="OK"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
            }
        }

    @staticmethod
    def create_shop_config():
        return {
            "description": "Создание магазина для продавца",
            "summary": "Создание магазина для продавца",
            "tags": ["Продавец"],
            "operation_id": "create_shop",
            "deprecated": False,
            "request": ShopSerializer,
            "responses":
            {
                status.HTTP_201_CREATED: OpenApiResponse(response={}, description="Created"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
            }
        }

    @staticmethod
    def get_seller_status_config():
        return {
            "description": "Получить текущий статус магазина",
            "summary": "Получить текущий статус магазина",
            "tags": ["Продавец"],
            "operation_id": "get_seller_status",
            "deprecated": False,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response=ShopSerializer, description="OK"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
            }
        }

    @staticmethod
    def change_seller_status_config():
        return {
            "description": "Изменение текущего статуса магазина",
            "summary": "Изменение текущего статуса магазина",
            "tags": ["Продавец"],
            "operation_id": "change_seller_status",
            "deprecated": False,
            "request": {
                "schema": {
                    "type": "boolean",
                    "parameters": ["is_active"]
                }
            },
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
            }
        }

    @staticmethod
    def get_shops_config():
        return {
            "description": "Получить список всех магазинов",
            "summary": "Получить список всех магазинов",
            "tags": ["Магазины"],
            "operation_id": "get_shops",
            "deprecated": False,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response=ShopSerializer, description="OK"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
            }
        }

    @staticmethod
    def get_users_account_config():
        return {
            "description": "Получить информацию об аккаунте пользователя",
            "summary": "Получить информацию об аккаунте пользователя",
            "tags": ["Пользователи"],
            "operation_id": "get_users_account",
            "deprecated": False,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response=UserSerializer, description="OK"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
            }
        }

    @staticmethod
    def change_users_account_config():
        return {
            "description": "Изменение информации об аккаунте пользователя",
            "summary": "Изменение информации об аккаунте пользователя",
            "tags": ["Пользователи"],
            "operation_id": "change_users_account",
            "deprecated": False,
            "request": UserSerializer,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
            }
        }

    @staticmethod
    def get_contact_config():
        return {
            "description": "Получить информацию о контакте пользователя",
            "summary": "Получить информацию о контакте пользователя",
            "tags": ["Пользователи"],
            "operation_id": "get_сontact",
            "deprecated": False,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response=ContactSerializer, description="OK"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
            }
        }

    @staticmethod
    def create_contact_config():
        return {
            "description": "Создание контакта пользователя",
            "summary": "Создание контакта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "create_сontact",
            "deprecated": False,
            "request": ContactSerializer,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized")
            }
        }

    @staticmethod
    def update_contact_config():
        return {
            "description": "Обновление контакта пользователя",
            "summary": "Обновление контакта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "update_сontact",
            "deprecated": False,
            "request": ContactSerializer,
            "responses":
            {
                status.HTTP_200_OK: OpenApiResponse(response={}, description="OK"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_404_NOT_FOUND: OpenApiResponse(response={}, description="Not found")
            }
        }

    @staticmethod
    def delete_contact_config():
        return {
            "description": "Удаление контакта пользователя",
            "summary": "Удаление контакта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "delete_сontact",
            "deprecated": False,
            "request": ObjectIDSerializer,
            "responses":
            {
                status.HTTP_204_NO_CONTENT: OpenApiResponse(response={}, description="No content"),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(response={}, description="Bad request"),
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response={}, description="Unauthorized"),
                status.HTTP_409_CONFLICT: OpenApiResponse(response={}, description="Conflict")
            }
        }
