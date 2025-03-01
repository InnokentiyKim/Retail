from rest_framework import serializers
from drf_spectacular.utils import OpenApiResponse, OpenApiParameter, OpenApiTypes
from backend.serializers import OrderSerializer, OrderConfirmSerializer, \
    OrderItemCreateUpdateSerializer, OrderItemUpdateSerializer, OrderItemDeleteSerializer, \
    CouponSerializer, OrderStateSerializer, ProductItemSerializer, ProductSerializer, \
    ShopSerializer, UserSerializer, ContactSerializer, ContactUpdateSerializer, CategorySerializer, \
    ContactDeleteSerializer, CouponDeleteSerializer, UserCreateSerializer, ContactCreateSerializer, \
    CouponCreateSerializer
from rest_framework import status



class APIRequestSchema:
    class ImportGoods(serializers.Serializer):
        url = serializers.URLField()

    class ChangeSellerStatus(serializers.Serializer):
        is_active = serializers.BooleanField()

    class ConfirmUserAccount(serializers.Serializer):
        email = serializers.EmailField()
        token = serializers.CharField(max_length=60)

    class TokenObtainRequest(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()

    class TokenRefresh(serializers.Serializer):
        refresh = serializers.CharField()

    class ResetPassword(serializers.Serializer):
        email = serializers.EmailField()

    class ConfirmResetPassword(serializers.Serializer):
        password = serializers.CharField()
        token = serializers.CharField(max_length=60)



class OKResponse(serializers.Serializer):
    success = serializers.BooleanField(default=True)


class ErrorResponse(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    error = serializers.CharField()


class APIResponseSchema:

    @staticmethod
    def get_response_object(error=False, error_msg='', serializer=None):
        if error:
            return ErrorResponse(error_msg)
        if serializer is not None:
            return {status.HTTP_200_OK: serializer}
        return OKResponse()

    responses = {
        200: {status.HTTP_200_OK: OpenApiResponse(response=get_response_object(), description="OK")},
        201: {status.HTTP_201_CREATED: OpenApiResponse(response=get_response_object(), description="Created")},
        204: {status.HTTP_204_NO_CONTENT: OpenApiResponse(response=get_response_object(), description="No content")},
        400: {status.HTTP_400_BAD_REQUEST: OpenApiResponse(response=get_response_object(
            True, "Bad request"), description="Bad request")},
        401: {status.HTTP_401_UNAUTHORIZED: OpenApiResponse(response=get_response_object(
            True, "Authentication credentials were not provided."), description="Unauthorized")},
        403: {status.HTTP_403_FORBIDDEN: OpenApiResponse(response=get_response_object(
            True, "Access denied"), description="Forbidden")},
        404: {status.HTTP_404_NOT_FOUND: OpenApiResponse(response=get_response_object(
            True, "Object not found"), description="Not found")},
        409: {status.HTTP_409_CONFLICT: OpenApiResponse(response=get_response_object(
            True, "Object saving error"), description="Conflict")},
        429: {status.HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(response=get_response_object(
            True, "Too many requests"), description="Too many requests")},
        500: {status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(response=get_response_object(
            True, "Server error"), description="Internal server error")}
    }

    class TokenObtainResponse(serializers.Serializer):
        access = serializers.CharField()
        refresh = serializers.CharField()

    @staticmethod
    def get_response_list(response_codes: list[int], responses_dict: dict, serializer=None) -> dict:
        response_list = {}
        for error_code in response_codes:
            if error_code == 200 and serializer is not None:
                response_list.update(APIResponseSchema.get_response_object(serializer=serializer))
            else:
                response_list.update(responses_dict.get(error_code))
        return response_list


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
                OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False,
                                 description="Фильтр по id категории"),
                OpenApiParameter(name="search", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False,
                                 description="Поиск по названию категории"),
                OpenApiParameter(name="ordering", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False,
                                 description="Сортировка по id или name")
            ],
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses, CategorySerializer)
        }

    @staticmethod
    def get_buyer_orders():
        return {
            "description": "Получить историю заказов покупателя",
            "summary": "Получить историю заказов покупателя",
            "tags": ["Покупатель"],
            "operation_id": "get_buyer_orders",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, OrderSerializer)
        }

    @staticmethod
    def confirm_buyer_order_config():
        return {
            "description": "Подтверждение заказа покупателя. В теле запроса передается id заказа, id контакта и "
                           "код купона (опционально)",
            "summary": "Подтверждение заказа покупателя",
            "tags": ["Покупатель"],
            "operation_id": "confirm_buyer_order",
            "deprecated": False,
            "parameters": None,
            "request": OrderConfirmSerializer,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_shopping_cart_config():
        return {
            "description": "Получить список товаров в корзине",
            "summary": "Получить список товаров в корзине",
            "tags": ["Покупатель"],
            "operation_id": "get_shopping_cart",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, OrderSerializer)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
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
            "responses": APIResponseSchema.get_response_list([204, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_coupons_config():
        return {
            "description": "Получить список скидочных купонов",
            "summary": "Получить список скидочных купонов",
            "tags": ["Менеджер"],
            "operation_id": "get_coupons",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, CouponSerializer)
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
            "responses": APIResponseSchema.get_response_list([201, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def update_coupon_config():
        return {
            "description": "Обновление скидочного купона",
            "summary": "Обновление скидочного купона",
            "tags": ["Менеджер"],
            "operation_id": "update_coupon",
            "deprecated": False,
            "request": CouponCreateSerializer,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def delete_coupon_config():
        return {
            "description": "Удаление скидочного купона",
            "summary": "Удаление скидочного купона",
            "tags": ["Менеджер"],
            "operation_id": "delete_coupon",
            "deprecated": False,
            "request": CouponDeleteSerializer,
            "responses": APIResponseSchema.get_response_list([204, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_manager_orders_config():
        return {
            "description": "Получить список заказов",
            "summary": "Получить список заказов",
            "tags": ["Менеджер"],
            "operation_id": "get_manager_orders",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, OrderSerializer)
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
            "responses": APIResponseSchema.get_response_list([200, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
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
                OpenApiParameter(name="shop_id", type=OpenApiTypes.INT, location='query', required=False,
                                 description="Фильтр по id магазина"),
                OpenApiParameter(name="category_id", type=OpenApiTypes.INT, location='query', required=False,
                                 description="Фильтр по id категории товаров"),
                OpenApiParameter(name="search", type=OpenApiTypes.STR, location='query', required=False,
                                 description="Поиск по названию товара"),
                OpenApiParameter(name="ordering", type=OpenApiTypes.STR, location='query', required=False,
                                 description="Сортировка по id или price (цене)")
            ],
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses, ProductItemSerializer)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses, ProductSerializer)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_seller_orders_config():
        return {
            "description": "Получить список заказов продавца",
            "summary": "Получить список заказов продавца",
            "tags": ["Продавец"],
            "operation_id": "get_seller_orders",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, OrderSerializer)
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
            "responses": APIResponseSchema.get_response_list([201, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_seller_status_config():
        return {
            "description": "Получить текущий статус магазина",
            "summary": "Получить текущий статус магазина",
            "tags": ["Продавец"],
            "operation_id": "get_seller_status",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses, ShopSerializer)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_shops_config():
        return {
            "description": "Получить список всех магазинов",
            "summary": "Получить список всех магазинов",
            "tags": ["Магазины"],
            "operation_id": "get_shops",
            "deprecated": False,
            "parameters": [
                OpenApiParameter(name="id", type=OpenApiTypes.INT, location='query', required=False,
                                 description="Фильтр по id магазина"),
                OpenApiParameter(name="search", type=OpenApiTypes.STR, location='query', required=False,
                                 description="Поиск по названию магазина"),
                OpenApiParameter(name="ordering", type=OpenApiTypes.STR, location='query', required=False,
                                 description="Сортировка по id или name (названию магазина)")
            ],
            "responses": APIResponseSchema.get_response_list([200, 400, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, ShopSerializer)
        }

    @staticmethod
    def get_seller_products_config():
        return {
            "description": "Получить список всех товаров магазина",
            "summary": "Получить список всех товаров магазина",
            "tags": ["Продавец"],
            "operation_id": "get_seller_products",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 400, 403, 404, 429, 500],
                                                             APIResponseSchema.responses, serializer=ProductItemSerializer)
        }

    @staticmethod
    def get_users_account_config():
        return {
            "description": "Получить информацию об аккаунте пользователя",
            "summary": "Получить информацию об аккаунте пользователя",
            "tags": ["Пользователи"],
            "operation_id": "get_users_account",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 401, 404, 429, 500],
                                                             APIResponseSchema.responses, UserSerializer)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def get_contact_config():
        return {
            "description": "Получить информацию о контактах пользователя",
            "summary": "Получить информацию о контактах пользователя",
            "tags": ["Пользователи"],
            "operation_id": "get_сontact",
            "deprecated": False,
            "responses": APIResponseSchema.get_response_list([200, 401, 404, 429, 500],
                                                             APIResponseSchema.responses, ContactSerializer)
        }

    @staticmethod
    def create_contact_config():
        return {
            "description": "Создание контакта пользователя",
            "summary": "Создание контакта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "create_сontact",
            "deprecated": False,
            "request": ContactCreateSerializer,
            "responses": APIResponseSchema.get_response_list([201, 400, 401, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def update_contact_config():
        return {
            "description": "Обновление контакта пользователя",
            "summary": "Обновление контакта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "update_сontact",
            "deprecated": False,
            "request": ContactUpdateSerializer,
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 403, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def delete_contact_config():
        return {
            "description": "Удаление контакта пользователя",
            "summary": "Удаление контакта пользователя",
            "tags": ["Пользователи"],
            "operation_id": "delete_сontact",
            "deprecated": False,
            "request": ContactDeleteSerializer,
            "responses": APIResponseSchema.get_response_list([204, 400, 401, 403, 404, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def user_register_config():
        return {
            "description": "Регистрация нового пользователя",
            "summary": "Регистрация нового пользователя",
            "tags": ["Пользователи"],
            "operation_id": "user_register",
            "deprecated": False,
            "request": UserCreateSerializer,
            "responses": APIResponseSchema.get_response_list([201, 400, 401, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 401, 404, 409, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def token_obtain_config():
        return {
            "description": "Получение пары access/refresh токенов",
            "summary": "Получение токена доступа",
            "tags": ["Пользователи"],
            "operation_id": "token_obtain",
            "deprecated": False,
            "request": APIRequestSchema.TokenObtainRequest,
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses, APIResponseSchema.TokenObtainResponse)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses, APIResponseSchema.TokenObtainResponse)
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
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses)
        }

    @staticmethod
    def confirm_reset_password_config():
        return {
            "description": "Подтверждение сброса пароля пользователя",
            "summary": "Подтверждение сброса пароля пользователя",
            "tags": ["Пользователи"],
            "operation_id": "confirm_reset_password",
            "deprecated": False,
            "request": APIRequestSchema.ConfirmResetPassword,
            "responses": APIResponseSchema.get_response_list([200, 400, 404, 429, 500],
                                                             APIResponseSchema.responses)
        }
