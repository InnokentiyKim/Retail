from django.http import JsonResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.request import Request
from .backend import UserBackend, ProductsBackend, SellerBackend, BuyerBackend, ContactBackend
from .models import Shop, Category
from .permissions import IsSeller, IsBuyer
from .serializers import CategorySerializer, ShopSerializer
from .signals import new_order
from .tasks import import_goods
from rest_framework import status as http_status


class AccountRegisterView(APIView):
    def post(self, request: Request):
        UserBackend.register_account(request)


class AccountConfirmView(APIView):
    def post(self, request):
        UserBackend.confirm_account(request)


class AccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        UserBackend.get_account_info(request)

    def post(self, request):
        UserBackend.change_account_info(request)


class SellerGoodsView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def post(self, request, *args, **kwargs):
        import_goods.delay(request)


class CategoryView(ListAPIView):
    permission_classes = (AllowAny,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    permission_classes = (AllowAny,)
    queryset = Shop.objects.filter(is_active=True)
    serializer_class = ShopSerializer


class ProductItemView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        ProductsBackend.get_products(request)


class ShoppingCartView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        BuyerBackend.get_shopping_cart(request)

    def post(self, request, *args, **kwargs):
        BuyerBackend.create_update_shopping_cart(request)

    def put(self, request, *args, **kwargs):
        BuyerBackend.update_shopping_cart(request)

    def delete(self, request, *args, **kwargs):
        BuyerBackend.delete_shopping_cart_items(request)


class SellerStatusView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        SellerBackend.get_status(request)

    def post(self, request, *args, **kwargs):
        SellerBackend.change_status(request)


class SellerOrdersView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        SellerBackend.get_orders(request)


class ContactView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        ContactBackend.get_contact(request)

    def post(self, request, *args, **kwargs):
        ContactBackend.create_contact(request)

    def put(self, request, *args, **kwargs):
        ContactBackend.update_contact(request)

    def delete(self, request, *args, **kwargs):
        ContactBackend.delete_contact(request)


class OrderView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        BuyerBackend.get_order(request)

    def post(self, request, *args, **kwargs):
        is_order_confirmed = BuyerBackend.confirm_order(request)
        if is_order_confirmed:
            new_order.send(sender=self.__class__, user_id=request.user.id)
            return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=http_status.HTTP_400_BAD_REQUEST)
