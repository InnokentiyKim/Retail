from rest_framework import serializers
from drf_spectacular.utils import OpenApiResponse, OpenApiParameter
from backend.serializers import CategorySerializer, OrderSerializer, OrderConfirmSerializer, \
    OrderItemCreateUpdateSerializer, OrderItemUpdateSerializer, OrderItemDeleteSerializer, \
    CouponSerializer, ObjectIDSerializer, OrderStateSerializer, ProductItemSerializer, ProductSerializer, \
    ShopSerializer, UserSerializer, ContactSerializer
from rest_framework import status



class APIRequestSchema:
    class ImportGoods(serializers.Serializer):
        url = serializers.URLField()

    class ChangeSellerStatus(serializers.Serializer):
        is_active = serializers.BooleanField()

    class ConfirmUserAccount(serializers.Serializer):
        email = serializers.EmailField()
        token = serializers.CharField(max_length=60)

    class TokenObtain(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()

    class TokenRefresh(serializers.Serializer):
        refresh = serializers.CharField()

    class ResetPassword(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()


class APIResponseSchema:

    class Response200(serializers.Serializer):
        success = serializers.BooleanField(default=True)

    class Response201(serializers.Serializer):
        success = serializers.BooleanField(default=True)

    class Response204(serializers.Serializer):
        success = serializers.BooleanField(default=True)

    class Response400(serializers.Serializer):
        success = serializers.BooleanField(default=False)
        error = serializers.JSONField(default=dict)

    class Response401(serializers.Serializer):
        success = serializers.BooleanField(default=False)
        error = serializers.JSONField(default=dict)

    class Response404(serializers.Serializer):
        success = serializers.BooleanField(default=False)
        error = serializers.JSONField(default=dict)

    class Response409(serializers.Serializer):
        success = serializers.BooleanField(default=False)
        error = serializers.JSONField(default=dict)

    class TokenObtain(serializers.Serializer):
        access = serializers.CharField()
        refresh = serializers.CharField()

    @staticmethod
    def create_response_list():
        return {
            status.HTTP_201_CREATED: OpenApiResponse(response=APIResponseSchema.Response201, description="Created"),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(response=APIResponseSchema.Response400, description="Bad request"),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response=APIResponseSchema.Response401, description="Unauthorized"),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(response=APIResponseSchema.Response404, description="Not found"),
            status.HTTP_409_CONFLICT: OpenApiResponse(response=APIResponseSchema.Response409, description="Conflict")
        }

    @staticmethod
    def get_response_list(response_serializer, use_auth=True):
        response_list = {
            status.HTTP_200_OK: OpenApiResponse(response=response_serializer, description="OK"),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(response=APIResponseSchema.Response400, description="Bad request"),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response=APIResponseSchema.Response401, description="Unauthorized"),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(response=APIResponseSchema.Response404, description="Not found"),
        }
        if use_auth is False:
            response_list.pop(status.HTTP_401_UNAUTHORIZED)
        return response_list

    @staticmethod
    def update_response_list():
        return APIResponseSchema.create_response_list()

    @staticmethod
    def delete_response_list():
        return {
            status.HTTP_204_NO_CONTENT: OpenApiResponse(response=APIResponseSchema.Response204, description="No content"),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(response=APIResponseSchema.Response400, description="Bad request"),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response=APIResponseSchema.Response401, description="Unauthorized"),
            status.HTTP_409_CONFLICT: OpenApiResponse(response=APIResponseSchema.Response409, description="Conflict")
        }



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
                OpenApiParameter(name="filter", type=str, location=OpenApiParameter.QUERY, required=False, description="Фильтр по id или названию"),
                OpenApiParameter(name="search", type=str, location=OpenApiParameter.QUERY, required=False, description="Поиск по названию"),
                OpenApiParameter(name="ordering", type=str, location=OpenApiParameter.QUERY, required=False, description="Сортировка по id или названию")
            ],
            "responses": APIResponseSchema.get_response_list(CategorySerializer, use_auth=False)
        }

    @staticmethod
    def get_buyer_orders():
        return {
            "description": "Получить историю заказов покупателя",
            "summary": "Получить историю заказов покупателя",
            "tags": ["Покупатель"],
            "operation_id": "get_buyer_orders",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(OrderSerializer)
        }

    @staticmethod
    def confirm_buyer_order_config():
        return {
            "description": "Подтверждение заказа покупателя. В теле запроса передается id заказа, id контакта и код купона (опционально)",
            "summary": "Подтверждение заказа покупателя",
            "tags": ["Покупатель"],
            "operation_id": "confirm_buyer_order",
            "deprecated": False,
            "parameters": None,
            "request": OrderConfirmSerializer,
            "responses": APIResponseSchema.create_response_list()
        }

    @staticmethod
    def get_shopping_cart_config():
        return {
            "description": "Получить список товаров в корзине",
            "summary": "Получить список товаров в корзине",
            "tags": ["Покупатель"],
            "operation_id": "get_shopping_cart",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(OrderSerializer)
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
            "responses": APIResponseSchema.create_response_list()
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
            "responses": APIResponseSchema.update_response_list()
        }

    @staticmethod
    def delete_shopping_cart_config():
        return {
            "description": "Удаление товаров из корзины покупателя",
            "summary": "Удаление товаров из корзины покупателя",
            "tags": ["Покупатель"],
            "operation_id": "delete_shopping_cart",
            "deprecated": False,
            "request": OrderItemDeleteSerializer(many=True),
            "responses": APIResponseSchema.delete_response_list()
        }

    @staticmethod
    def get_coupons_config():
        return {
            "description": "Получить список скидочных купонов",
            "summary": "Получить список скидочных купонов",
            "tags": ["Менеджер"],
            "operation_id": "get_coupons",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(CouponSerializer)
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
            "responses": APIResponseSchema.create_response_list()
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
            "responses": APIResponseSchema.update_response_list()
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
            "responses": APIResponseSchema.delete_response_list()
        }

    @staticmethod
    def get_manager_orders_config():
        return {
            "description": "Получить список заказов",
            "summary": "Получить список заказов",
            "tags": ["Менеджер"],
            "operation_id": "get_manager_orders",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(OrderSerializer)
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
            "responses": APIResponseSchema.update_response_list()
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
                OpenApiParameter(name="filter", type=str, location='query', required=False,
                                 description="Фильтр по id магазина или категории товаров"),
                OpenApiParameter(name="search", type=str, location='query', required=False,
                                 description="Поиск по названию"),
                OpenApiParameter(name="ordering", type=str, location='query', required=False,
                                 description="Сортировка по id, названию товара, магазина или цене")
            ],
            "responses": APIResponseSchema.get_response_list(ProductItemSerializer, use_auth=False)
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
                OpenApiParameter(name="amount", type=int, location='query', required=False,
                                 description="Количество популярных товаров")
            ],
            "responses": APIResponseSchema.get_response_list(ProductSerializer, use_auth=False)
        }

    @staticmethod
    def import_seller_goods_config():
        return {
            "description": "Импорт товаров магазина",
            "summary": "Импорт товаров магазина",
            "tags": ["Продавец"],
            "operation_id": "import_seller_products",
            "deprecated": False,
            "request": APIRequestSchema.ImportGoods,
            "responses": APIResponseSchema.get_response_list(APIResponseSchema.Response200)
        }

    @staticmethod
    def get_seller_orders_config():
        return {
            "description": "Получить список заказов продавца",
            "summary": "Получить список заказов продавца",
            "tags": ["Продавец"],
            "operation_id": "get_seller_orders",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(OrderSerializer)
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
            "responses": APIResponseSchema.create_response_list()
        }

    @staticmethod
    def get_seller_status_config():
        return {
            "description": "Получить текущий статус магазина",
            "summary": "Получить текущий статус магазина",
            "tags": ["Продавец"],
            "operation_id": "get_seller_status",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(ShopSerializer)
        }

    @staticmethod
    def change_seller_status_config():
        return {
            "description": "Изменение текущего статуса магазина",
            "summary": "Изменение текущего статуса магазина",
            "tags": ["Продавец"],
            "operation_id": "change_seller_status",
            "deprecated": False,
            "request": APIRequestSchema.ChangeSellerStatus,
            "responses": APIResponseSchema.update_response_list()
        }

    @staticmethod
    def get_shops_config():
        return {
            "description": "Получить список всех магазинов",
            "summary": "Получить список всех магазинов",
            "tags": ["Магазины"],
            "operation_id": "get_shops",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(ShopSerializer)
        }

    @staticmethod
    def get_users_account_config():
        return {
            "description": "Получить информацию об аккаунте пользователя",
            "summary": "Получить информацию об аккаунте пользователя",
            "tags": ["Пользователи"],
            "operation_id": "get_users_account",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(UserSerializer)
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
            "responses": APIResponseSchema.update_response_list()
        }

    @staticmethod
    def get_contact_config():
        return {
            "description": "Получить информацию о контакте пользователя",
            "summary": "Получить информацию о контакте пользователя",
            "tags": ["Пользователи"],
            "operation_id": "get_сontact",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list(ContactSerializer)
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
            "responses": APIResponseSchema.create_response_list()
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
            "responses": APIResponseSchema.update_response_list()
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
            "responses": APIResponseSchema.delete_response_list()
        }

    @staticmethod
    def user_register_config():
        return {
            "description": "Регистрация нового пользователя",
            "summary": "Регистрация нового пользователя",
            "tags": ["Пользователи"],
            "operation_id": "user_register",
            "deprecated": False,
            "request": UserSerializer,
            "responses": APIResponseSchema.create_response_list()
        }

    @staticmethod
    def confirm_user_account_config():
        return {
            "description": "Подтверждение аккаунта пользователя",
            "summary": "Подтверждение аккаунта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "confirm_user_account",
            "deprecated": False,
            "request": APIRequestSchema.ConfirmUserAccount,
            "responses": APIResponseSchema.update_response_list()
        }

    @staticmethod
    def token_obtain_config():
        return {
            "description": "Получение пары access/refresh токенов",
            "summary": "Получение токена доступа",
            "tags": ["Пользователи"],
            "operation_id": "token_obtain",
            "deprecated": False,
            "request": APIRequestSchema.TokenObtain,
            "responses": APIResponseSchema.get_response_list(APIResponseSchema.TokenObtain)
        }

    @staticmethod
    def token_refresh_config():
        return {
            "description": "Повторное получение пары access/refresh токенов",
            "summary": "Повторное получение токена доступа",
            "tags": ["Пользователи"],
            "operation_id": "token_refresh",
            "deprecated": False,
            "request": APIRequestSchema.TokenRefresh,
            "responses": APIResponseSchema.get_response_list(APIResponseSchema.TokenObtain)
        }

    @staticmethod
    def reset_password_config():
        return {
            "description": "Сброс пароля пользователя",
            "summary": "Сброс пароля пользователя",
            "tags": ["Пользователи"],
            "operation_id": "reset_password",
            "deprecated": False,
            "request": APIRequestSchema.ResetPassword,
            "responses": APIResponseSchema.update_response_list()
        }

    @staticmethod
    def confirm_reset_password_config():
        return {
            "description": "Подтверждение сброса пароля пользователя",
            "summary": "Подтверждение сброса пароля пользователя",
            "tags": ["Пользователи"],
            "operation_id": "confirm_reset_password",
            "deprecated": False,
            "request": APIRequestSchema.ConfirmUserAccount,
            "responses": APIResponseSchema.update_response_list()
        }
