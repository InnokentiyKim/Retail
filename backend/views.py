from django.http import JsonResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.request import Request
from .backend import UserBackend, ProductsBackend, SellerBackend, BuyerBackend, ContactBackend, CouponBackend
from .filters import ProductItemFilter
from .models import Shop, Category
from .permissions import IsSeller, IsBuyer
from .serializers import CategorySerializer, ShopSerializer, UserSerializer
from .signals import new_order
from .tasks import import_goods
from rest_framework import status as http_status
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
        return import_goods.delay(request)


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


class SellerShopView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        return SellerBackend.get_shop(request)

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
        return ContactBackend.get_contact(request)

    def post(self, request, *args, **kwargs):
        return ContactBackend.create_contact(request)

    def put(self, request, *args, **kwargs):
        return ContactBackend.update_contact(request)

    def delete(self, request, *args, **kwargs):
        return ContactBackend.delete_contact(request)


class OrderView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        return BuyerBackend.get_order(request)

    def post(self, request, *args, **kwargs):
        is_order_confirmed = BuyerBackend.confirm_order(request)
        if is_order_confirmed:
            new_order.send(sender=self.__class__, user_id=request.user.id)
            return JsonResponse({'status': True}, status=200)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)


class CouponView(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        return CouponBackend.get_coupons(request)

    def post(self, request, *args, **kwargs):
        return CouponBackend.create_coupon(request)

    def delete(self, request, *args, **kwargs):
        return CouponBackend.delete_coupon(request)
