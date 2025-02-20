from re import search

from django.core.cache import cache
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.request import Request
from .backend import UserBackend, ProductsBackend, SellerBackend, BuyerBackend, ContactBackend, CouponBackend, \
    ManagerBackend
from .filters import ProductItemFilter
from .models import Shop, Category
from .permissions import IsSeller, IsBuyer
from .serializers import CategorySerializer, ShopSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


class AccountRegisterView(APIView):
    def post(self, request: Request):
        return UserBackend.register_account(request)


class AccountConfirmView(APIView):
    def post(self, request):
        return UserBackend.confirm_account(request)


class AccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return UserBackend.get_account_info(request)

    def post(self, request):
        return UserBackend.change_account_info(request)


class SellerGoodsView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def post(self, request, *args, **kwargs):
        return SellerBackend.import_seller_goods(request, args, kwargs)


class CategoriesView(ListAPIView):
    permission_classes = (AllowAny,)

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['id', 'name']
    search_fields = ['name']
    ordering_fields = ['id', 'name']


class ShopsView(ListAPIView):
    permission_classes = (AllowAny,)

    queryset = Shop.objects.filter(is_active=True)
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['id', 'name']
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name']

    @cache_page(60 * 15)
    def get(self, request, *args, **kwargs):
        cache_key = self.get_cache_key(request, **kwargs)
        result = cache.get(cache_key)
        if not result:
            result = super().get(request, *args, **kwargs)
            if result is not None:
                cache.set(cache_key, result.data, 60 * 15)
        return result

    @staticmethod
    def get_cache_key(request, **kwargs):
        used_filters = request.GET.get('filters', '')
        used_search = request.GET.get('search', '')
        used_ordering = request.GET.get('ordering', '')
        return f'shops_{used_filters}_{used_search}_{used_ordering}'


class SellerShopView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def post(self, request, *args, **kwargs):
        return SellerBackend.create_shop(request)


class ProductItemView(APIView):
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductItemFilter

    def get(self, request, *args, **kwargs):
        return ProductsBackend.get_products(self, request)


class ShoppingCartView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        return BuyerBackend.get_shopping_cart(request)

    def post(self, request, *args, **kwargs):
        return BuyerBackend.create_update_shopping_cart(request)

    def put(self, request, *args, **kwargs):
        return BuyerBackend.update_shopping_cart(request)

    def delete(self, request, *args, **kwargs):
        return BuyerBackend.delete_shopping_cart_items(request)


class SellerStatusView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        return SellerBackend.get_status(request)

    def post(self, request, *args, **kwargs):
        return SellerBackend.change_status(request)


class SellerOrdersView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        return SellerBackend.get_orders(request)


class ContactView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return ContactBackend.get_contacts(request)

    def post(self, request, *args, **kwargs):
        return ContactBackend.create_contact(request)

    def put(self, request, *args, **kwargs):
        return ContactBackend.update_contact(request)

    def delete(self, request, *args, **kwargs):
        return ContactBackend.delete_contact(request)


class BuyerOrdersView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        return BuyerBackend.get_orders(request)

    def post(self, request, *args, **kwargs):
        return BuyerBackend.confirm_order(request, sender=self.__class__)


class CouponView(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        return ManagerBackend.get_coupons(request)

    def post(self, request, *args, **kwargs):
        return ManagerBackend.create_coupon(request)

    def put(self, request, *args, **kwargs):
        return ManagerBackend.update_coupon(request)

    def delete(self, request, *args, **kwargs):
        return ManagerBackend.delete_coupon(request)


class ManagerOrdersView(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        return ManagerBackend.get_orders(request)

    def put(self, request, *args, **kwargs):
        return ManagerBackend.change_orders_state(request)
