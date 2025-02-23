from django.core.cache import cache
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.request import Request
from .backend import UserBackend, ProductsBackend, SellerBackend, BuyerBackend, ContactBackend, ManagerBackend
from .filters import ProductItemFilter
from .models import Shop, Category
from .permissions import IsSeller, IsBuyer
from .serializers import CategorySerializer, ShopSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


class AccountRegisterView(APIView):
    """
    Представление для регистрации нового пользователя
    """
    def post(self, request: Request):
        return UserBackend.register_account(request)


class AccountConfirmView(APIView):
    """
    Представление для подтверждения аккаунта по токену
    """
    def post(self, request):
        return UserBackend.confirm_account(request)


class AccountView(APIView):
    """
    Представление для обновления/получения информации об аккаунте пользователя
    Доступно только для авторизованного пользователя
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return UserBackend.get_account_info(request)

    def post(self, request):
        return UserBackend.change_account_info(request)


class SellerGoodsView(APIView):
    """
    Представление для импорта товаров магазина продавца
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

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
    filterset_fields = ['id', 'name']
    search_fields = ['name']
    ordering_fields = ['id', 'name']


class ShopsView(ListAPIView):
    """
    Представление для получения списка магазинов
    Доступны фильтры, поиск и сортировка по названию и описанию, указанные в GET-параметрах запроса
    """
    permission_classes = (AllowAny,)

    queryset = Shop.objects.filter(is_active=True)
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['id', 'name']
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name']

    @staticmethod
    def get_cache_key(request, **kwargs):
        """
        Функция для получения ключа кэша
        """
        used_filters = request.GET.get('filters', '')
        used_search = request.GET.get('search', '')
        used_ordering = request.GET.get('ordering', '')
        return f'shops_{used_filters}_{used_search}_{used_ordering}'

    def get(self, request, *args, **kwargs):
        """
        Переопределение метода получения списка магазинов
        Метод использует кэширование результатов запроса
        """
        cache_key = self.get_cache_key(request, **kwargs)
        result = cache.get(cache_key)
        if not result:
            result = super().get(request, *args, **kwargs)
            if result is not None:
                cache.set(cache_key, result.data, 60 * 10)
        return result


class SellerShopView(APIView):
    """
    Представление для создания магазина продавца
    Доступно только для авторизованного продавца
    """
    permission_classes = (IsAuthenticated, IsSeller)

    def post(self, request, *args, **kwargs):
        return SellerBackend.create_shop(request)


class ProductItemView(APIView):
    """
    Представление для получения списка товаров
    Доступны фильтры, поиск и сортировка, указанные в GET-параметрах запроса
    """
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductItemFilter

    def get(self, request, *args, **kwargs):
        return ProductsBackend.get_products(self, request)


class ShoppingCartView(APIView):
    """
    Представление для работы с корзиной покупателя
    Доступно только для авторизованного покупателя
    """
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        """
        Получение списка товаров в корзине
        """
        return BuyerBackend.get_shopping_cart(request)

    def post(self, request, *args, **kwargs):
        """
        Добавление товара в корзину
        """
        return BuyerBackend.create_update_shopping_cart(request)

    def put(self, request, *args, **kwargs):
        """
        Обновление количества товара в корзине
        """
        return BuyerBackend.update_shopping_cart(request)

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

    def get(self, request, *args, **kwargs):
        """
        Получение статуса продавца
        """
        return SellerBackend.get_status(request)

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

    def get(self, request, *args, **kwargs):
        return SellerBackend.get_orders(request)


class ContactView(APIView):
    """
    Представление для работы с контактами пользователя
    Доступно только для авторизованного пользователя
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        Получение списка контактов
        """
        return ContactBackend.get_contacts(request)

    def post(self, request, *args, **kwargs):
        """
        Создание контакта
        """
        return ContactBackend.create_contact(request)

    def put(self, request, *args, **kwargs):
        """
        Обновление контакта
        """
        return ContactBackend.update_contact(request)

    def delete(self, request, *args, **kwargs):
        """
        Удаление контакта
        """
        return ContactBackend.delete_contact(request)


class BuyerOrdersView(APIView):
    """
    Представление для получения/подтверждения заказа(-ов) покупателя
    Доступно только для авторизованного покупателя
    """
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        """
        Получение истории заказов
        """
        return BuyerBackend.get_orders(request)

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

    def get(self, request, *args, **kwargs):
        """
        Получение списка купонов
        """
        return ManagerBackend.get_coupons(request)

    def post(self, request, *args, **kwargs):
        """
        Создание купона
        """
        return ManagerBackend.create_coupon(request)

    def put(self, request, *args, **kwargs):
        """
        Обновление купона
        """
        return ManagerBackend.update_coupon(request)

    def delete(self, request, *args, **kwargs):
        """
        Удаление купона
        """
        return ManagerBackend.delete_coupon(request)


class ManagerOrdersView(APIView):
    """
    Представление для работы с заказами
    Доступно только для авторизованного администратора
    """
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        """
        Получение списка заказов
        """
        return ManagerBackend.get_orders(request)

    def put(self, request, *args, **kwargs):
        """
        Изменение статуса заказа
        """
        return ManagerBackend.change_orders_state(request)


class PopularProductsView(APIView):
    """
    Представление для получения списка наиболее популярных товаров
    """
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """
        Получение списка наиболее популярных товаров
        Параметр amount - количество популярных товаров, которое нужно получить
        """
        amount = request.GET.get('amount', None)
        if amount and amount.isdigit() and int(amount) > 0:
            return ProductsBackend.get_product_ranking(int(amount))
        return ProductsBackend.get_product_ranking(5)
