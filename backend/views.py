from django.http.response import JsonResponse
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django_rest_passwordreset.views import ResetPasswordRequestToken, ResetPasswordConfirm
from .backend import UserBackend, ProductsBackend, SellerBackend, BuyerBackend, ContactBackend, ManagerBackend
from .filters import ProductItemFilter
from .models import Shop, Category, ProductItem
from .permissions import IsSeller, IsBuyer
from .serializers import CategorySerializer, ShopSerializer, ProductItemSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .api_config import APIConfig
from cacheops import cached_as


class AccountRegisterView(APIView):
    """
    Представление для регистрации нового пользователя
    """

    @extend_schema(**APIConfig.user_register_config())
    def post(self, request: Request):
        return UserBackend.register_account(request)


class AccountConfirmView(APIView):
    """
    Представление для подтверждения аккаунта по токену
    """

    @extend_schema(**APIConfig.confirm_user_account_config())
    def post(self, request):
        return UserBackend.confirm_account(request)

class AccountResetPasswordView(ResetPasswordRequestToken):
    """
    Представление для сброса пароля
    """

    @extend_schema(**APIConfig.reset_password_config())
    def post(self, request):
        return super().post(request)

class AccountResetPasswordConfirmView(ResetPasswordConfirm):
    """
    Представление для подтверждения сброса пароля
    """

    @extend_schema(**APIConfig.confirm_reset_password_config())
    def post(self, request):
        return super().post(request)


class AccountView(APIView):
    """
    Представление для обновления/получения информации об аккаунте пользователя
    Доступно только для авторизованного пользователя
    """
    permission_classes = (IsAuthenticated,)

    @extend_schema(**APIConfig.get_users_account_config())
    def get(self, request):
        return UserBackend.get_account_info(request)

    @extend_schema(**APIConfig.change_users_account_config())
    def post(self, request):
        return UserBackend.change_account_info(request)


class TokenObtain(TokenObtainPairView):
    """
    Представление для получения JWT-токена
    Параметры: email(str) и password(str)
    Возращает: access(str) и refresh(str)
    """

    @extend_schema(**APIConfig.token_obtain_config())
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefresh(TokenRefreshView):
    """
    Представление для обновления JWT-токена
    Параметры: refresh(str)
    Возращает: access(str) и refresh(str)
    """

    @extend_schema(**APIConfig.token_refresh_config())
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SellerGoodsView(APIView):
    """
    Представление для импорта товаров магазина продавца
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

    @extend_schema(**APIConfig.import_seller_goods_config())
    def post(self, request, *args, **kwargs):
        return SellerBackend.import_seller_goods(request, args, kwargs)


class CategoriesView(ListAPIView):
    """
    Представление для получения списка категорий
    Доступны фильтры, поиск и сортировка по названию, указанные в GET-параметрах запроса
    """
    permission_classes = (AllowAny,)

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['id']
    search_fields = ['name']
    ordering_fields = ['id', 'name']

    @extend_schema(**APIConfig.get_category_config())
    def get(self, request, *args, **kwargs):
        response = super(CategoriesView, self).get(request, *args, **kwargs)
        categories = response.data
        return JsonResponse(categories)


class ShopsView(ListAPIView):
    """
    Представление для получения списка магазинов
    Доступны фильтры, поиск и сортировка по названию и описанию, указанные в GET-параметрах запроса
    """
    permission_classes = (AllowAny,)

    queryset = Shop.objects.filter(is_active=True)
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['id',]
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name']

    @extend_schema(**APIConfig.get_shops_config())
    def get(self, request, *args, **kwargs):
        """
        Переопределение метода получения списка магазинов
        Метод использует кэширование результатов запроса
        """
        shops = super().get(request, *args, **kwargs).data
        return JsonResponse(shops)


class SellerShopView(APIView):
    """
    Представление для создания магазина продавца
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

    @extend_schema(**APIConfig.create_shop_config())
    def post(self, request, *args, **kwargs):
        return SellerBackend.create_shop(request)


class ProductItemView(ListAPIView):
    """
    Представление для получения списка товаров
    Доступны фильтры, поиск и сортировка, указанные в GET-параметрах запроса
    """
    permission_classes = (AllowAny,)

    serializer_class = ProductItemSerializer
    queryset = ProductItem.objects.filter(shop__is_active=True, quantity__gt=0).select_related(
                'shop', 'product').distinct()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductItemFilter

    @extend_schema(**APIConfig.get_products_config())
    def get(self, request, *args, **kwargs):
        response = super(ProductItemView, self).get(request, *args, **kwargs)
        products = response.data
        return JsonResponse(products)


class ShoppingCartView(APIView):
    """
    Представление для работы с корзиной покупателя
    Доступно только для авторизованного покупателя
    """
    permission_classes = (IsAuthenticated, IsBuyer)

    @extend_schema(**APIConfig.get_shopping_cart_config())
    def get(self, request, *args, **kwargs):
        """
        Получение списка товаров в корзине
        """
        return BuyerBackend.get_shopping_cart(request)

    @extend_schema(**APIConfig.create_shopping_cart_config())
    def post(self, request, *args, **kwargs):
        """
        Добавление товара в корзину
        """
        return BuyerBackend.create_update_shopping_cart(request)

    @extend_schema(**APIConfig.update_shopping_cart_config())
    def put(self, request, *args, **kwargs):
        """
        Обновление количества товара в корзине
        """
        return BuyerBackend.update_shopping_cart(request)

    @extend_schema(**APIConfig.delete_shopping_cart_config())
    def delete(self, request, *args, **kwargs):
        """
        Удаление товара из корзины
        """
        return BuyerBackend.delete_shopping_cart_items(request)


class SellerStatusView(APIView):
    """
    Представление для изменения/получения статуса продавца
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

    @extend_schema(**APIConfig.get_seller_status_config())
    def get(self, request, *args, **kwargs):
        """
        Получение статуса продавца
        """
        @cached_as(Shop.objects.filter(user_id=request.user.id), timeout=60*30)
        def get_status():
            return SellerBackend.get_status(request)
        return get_status()

    @extend_schema(**APIConfig.change_seller_status_config())
    def post(self, request, *args, **kwargs):
        """
        Изменение статуса продавца
        """
        return SellerBackend.change_status(request)


class SellerOrdersView(APIView):
    """
    Представление для получения списка заказов поступивших продавцу
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

    @extend_schema(**APIConfig.get_seller_orders_config())
    def get(self, request, *args, **kwargs):
        return SellerBackend.get_orders(request)


class SellerProductsView(APIView):
    """
    Представление для получения списка товаров продавца
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

    @extend_schema(**APIConfig.get_seller_products_config())
    def get(self, request, *args, **kwargs):
        return SellerBackend.get_seller_products(request)


class ContactView(APIView):
    """
    Представление для работы с контактами пользователя
    Доступно только для авторизованного пользователя
    """
    permission_classes = (IsAuthenticated, (IsBuyer | IsSeller | IsAdminUser))

    @extend_schema(**APIConfig.get_contact_config())
    def get(self, request, *args, **kwargs):
        """
        Получение списка контактов
        """
        return ContactBackend.get_contacts(request)

    @extend_schema(**APIConfig.create_contact_config())
    def post(self, request, *args, **kwargs):
        """
        Создание контакта
        """
        return ContactBackend.create_contact(request)

    @extend_schema(**APIConfig.update_contact_config())
    def put(self, request, *args, **kwargs):
        """
        Обновление контакта
        """
        return ContactBackend.update_contact(request)

    @extend_schema(**APIConfig.delete_contact_config())
    def delete(self, request, *args, **kwargs):
        """
        Удаление контакта пользователя
        Параметр: <contact_id> - ID контакта для удаления (параметр пути).
        """
        return ContactBackend.delete_contact(request, *args, **kwargs)


class BuyerOrdersView(APIView):
    """
    Представление для получения/подтверждения заказа(-ов) покупателя
    Доступно только для авторизованного покупателя
    """
    permission_classes = (IsAuthenticated, IsBuyer)

    @extend_schema(**APIConfig.get_buyer_orders())
    def get(self, request, *args, **kwargs):
        """
        Получение истории заказов
        """
        return BuyerBackend.get_orders(request)

    @extend_schema(**APIConfig.confirm_buyer_order_config())
    def post(self, request, *args, **kwargs):
        """
        Подтверждение заказа
        """
        return BuyerBackend.confirm_order(request, sender=self.__class__)


class CouponView(APIView):
    """
    Представление для работы с купонами
    Доступно только для авторизованного администратора
    """
    permission_classes = (IsAuthenticated, IsAdminUser)

    @extend_schema(**APIConfig.get_coupons_config())
    def get(self, request, *args, **kwargs):
        """
        Получение списка купонов
        """
        return ManagerBackend.get_coupons(request)

    @extend_schema(**APIConfig.create_coupon_config())
    def post(self, request, *args, **kwargs):
        """
        Создание купона
        """
        return ManagerBackend.create_coupon(request)

    @extend_schema(**APIConfig.update_coupon_config())
    def put(self, request, *args, **kwargs):
        """
        Обновление купона
        """
        return ManagerBackend.update_coupon(request)

    @extend_schema(**APIConfig.delete_coupon_config())
    def delete(self, request, *args, **kwargs):
        """
        Удаление купона
        Параметр: items (list[int]) - список ID купонов для удаления
        """
        return ManagerBackend.delete_coupon(request, *args, **kwargs)


class ManagerOrdersView(APIView):
    """
    Представление для работы с заказами
    Доступно только для авторизованного администратора
    """
    permission_classes = (IsAuthenticated, IsAdminUser)

    @extend_schema(**APIConfig.get_manager_orders_config())
    def get(self, request, *args, **kwargs):
        """
        Получение списка заказов
        """
        return ManagerBackend.get_orders(request)

    @extend_schema(**APIConfig.update_manager_order_config())
    def put(self, request, *args, **kwargs):
        """
        Изменение статуса заказа
        """
        return ManagerBackend.change_orders_state(request, sender=self.__class__)


class PopularProductsView(APIView):
    """
    Представление для получения списка наиболее популярных товаров
    """
    permission_classes = (AllowAny,)

    @extend_schema(**APIConfig.get_popular_products_config())
    def get(self, request, *args, **kwargs):
        """
        Получение списка наиболее популярных товаров
        Параметр amount - количество популярных товаров, которое нужно получить
        """
        amount = request.GET.get('amount')
        if amount and amount.isdigit() and int(amount) > 0:
            return ProductsBackend.get_product_ranking(int(amount))
        else:
            return ProductsBackend.get_product_ranking(5)


def authorize_by_oauth(request):
    return render(request, 'oauth.html')

def oauth_complete_redirect(request):
    return render(request, 'oauth-success.html')
