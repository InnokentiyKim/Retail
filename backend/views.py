import json
import yaml
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Sum, F, Q
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status as http_status
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from .models import User, Shop, Category, Product, ProductItem, Order, OrderStateChoices, OrderItem, UserTypeChoices, \
    Contact, EmailTokenConfirm, Property, ProductProperty
from rest_framework.authtoken.models import Token
from .permissions import IsSeller, IsBuyer
from .serializers import CategorySerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, \
    ProductItemSerializer, ContactSerializer, UserSerializer
from backend.signals import new_user_registered, new_order


class AccountRegisterView(APIView):
    def post(self, request: Request):
        if {'email', 'username', 'first_name', 'last_name', 'password'}.issubset(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'error': str(error)}, status=400)
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'status': True}, status=201)
                else:
                    return JsonResponse({'status': False, 'errors': user_serializer.errors}, status=400)
        return JsonResponse({'status': False, }, status=400)


class AccountConfirmView(APIView):
    def post(self, request):
        if {'email', 'token'}.issubset(request.data):
            token = EmailTokenConfirm.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True}, status=200)
            else:
                return JsonResponse({'Status': False, 'error': 'Неверно указан email или токен'}, status=400)
        return JsonResponse({'Status': False}, status=400)


class LoginAccountView(APIView):
    def post(self, request):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user and user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return JsonResponse({'Status': True, 'token': token.key})
            return JsonResponse({'Status': False, 'error': 'Authentication failed'}, status=403)
        return JsonResponse({'Status': False}, status=400)


class AccountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'error': str(error)}, status=400)
            else:
                request.user.set_password(request.data['password'])
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True}, status=200)
        else:
            return JsonResponse({'Status': False, 'errors': user_serializer.errors}, status=400)


class SellerGoodsView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def post(self, request, *args, **kwargs):
        url = request.data.get('url', None)
        if url is None:
            return JsonResponse({'error': 'url is required'}, status=400)
        validate_url = URLValidator(verify_exists=True)
        try:
            validate_url(url)
        except ValidationError as error:
            return JsonResponse({'status': False, 'error': str(error)}, status=400)
        stream = get(url).content
        data = yaml.safe_load(stream)
        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
        for category in data['categories']:
            product_category, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
            product_category.shops.add(shop)
            product_category.save()
        for item in data['goods']:
            product, created = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
            product_item = ProductItem.objects.create(
                product_id=product.id,
                shop_id=shop.id,
                price=item['price'],
                price_retail=item['price_retail'],
                quantity=item['quantity']
            )
            for key, value in item['properties'].items():
                property_instance, _ = Property.objects.get_or_create(name=key)
                ProductProperty.objects.create(
                    product_item_id=product_item.id,
                    property_id=property_instance.id,
                    value=value
                )
        return JsonResponse({'Status': True}, status=200)


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
        query = Q(shop__is_active=True)
        shop_id = request.query_params.get('shop_id', None)
        category_id = request.query_params.get('category_id', None)
        if shop_id:
            query &= Q(shop__id=shop_id)
        if category_id:
            query &= Q(product__category_id=category_id)
        queryset = ProductItem.objects.filter(query).select_related(
            'shop', 'product__category').distinct()
        serializer = ProductItemSerializer(queryset, many=True)
        return Response(serializer.data)


class ShoppingCartView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request, *args, **kwargs):
        cart = Order.objects.filter(
            user_id=request.user.id).prefetch_related(
            'ordered_items__product__category').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('order_items__product__details__price'))).distinct()
        serializer = OrderSerializer(cart, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        updating_items = request.data.get('items')
        if updating_items is None:
            return JsonResponse({'error': 'items is required'}, status=400)
        try:
            updating_items_dict = json.loads(updating_items)
        except ValueError:
            return JsonResponse({'error': 'items format is invalid'}, status=400)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.CREATED)
        for item in updating_items_dict:
            item.update({'order_id': cart.id})
            serializer = OrderItemSerializer(item)
            if serializer.is_valid():
                try:
                    serializer.save()
                except IntegrityError as err:
                    return JsonResponse({'error': str(err)}, status=400)
            else:
                return JsonResponse({'error': serializer.errors}, status=400)
        return JsonResponse({'Status': True}, status=200)

    def put(self, request, *args, **kwargs):
        adding_items = request.data.get('items')
        if adding_items:
            try:
                adding_items_dict = json.loads(adding_items)
            except ValueError:
                return JsonResponse({'error': 'items format is invalid'}, status=400)
            cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.CREATED)
            for item in adding_items_dict:
                if type(item['id']) is int and type(item['quantity']) is int:
                    OrderItem.objects.filter(order_id=cart.id, id=item['id']).update(quantity=item['quantity'])
            return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=400)

    def delete(self, request, *args, **kwargs):
        deleting_items = request.data.get('items')
        if deleting_items:
            deleting_items_list = deleting_items.split(',')
            cart = Order.objects.filter(user_id=request.user.id, state=OrderStateChoices.CREATED)
            if cart:
                query = Q()
                has_deleting_items = False
                for item_id in deleting_items_list:
                    if item_id.isdigit():
                        query |= Q(order_id=cart.id, id=item_id)
                        has_deleting_items = True
                if has_deleting_items:
                    OrderItem.objects.filter(query).delete()
                    return JsonResponse({'Status': True}, status=204)
        return JsonResponse({'Status': False}, status=400)


class SellerStatusView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        seller_status = request.data.get('is_active')
        print(seller_status)
        if seller_status is not None:
            try:
                Shop.objects.filter(user_id=request.user.id).update(is_active=bool(seller_status))
                return JsonResponse({'Status': True}, status=200)
            except IntegrityError as db_err:
                return JsonResponse({'error': str(db_err)}, status=400)
            except ValueError as val_err:
                return JsonResponse({'error': str(val_err)}, status=400)
        return JsonResponse({'Status': False}, status=400)


class SellerOrdersView(APIView):
    permission_classes = (IsAuthenticated, IsSeller)

    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(
            ordered_items__product_item__shop__user_id=request.user.id).exclude(
            state=OrderStateChoices.PREPARING).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties').select_related(
            'contact').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product_item__price'))
        ).distinct()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class ContactView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if {'city', 'street', 'house', 'apartment', 'phone'}.issubset(request.data):
            contact_data = request.data.copy()
            contact_data.update({'user': request.user.id})
            serializer = ContactSerializer(data=contact_data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True}, status=201)
            return JsonResponse({'error': serializer.errors}, status=400)
        return JsonResponse({'Status': False}, status=400)

    def put(self, request, *args, **kwargs):
        if 'id' in request.data and request.data['id'].isdigit():
            contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
            if contact:
                serializer = ContactSerializer(contact, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'Status': True}, status=200)
                else:
                    return JsonResponse({'error': serializer.errors}, status=400)
        return JsonResponse({'Status': False}, status=400)

    def delete(self, request, *args, **kwargs):
        deleting_contacts = request.data.get('items')
        if deleting_contacts:
            deleting_contacts_list = deleting_contacts.split(',')
            query = Q()
            has_deleting_items = False
            for contact_id in deleting_contacts_list:
                if contact_id.isdigit():
                    query |= Q(user_id=request.user.id, id=contact_id)
                    has_deleting_items = True
            if has_deleting_items:
                Contact.objects.filter(query).delete()
                return JsonResponse({'Status': True}, status=204)
        return JsonResponse({'Status': False}, status=400)



class OrderView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(user_id=request.user.id).exclude(
            state=OrderStateChoices.CREATED).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('order_items__product_item__price'))
        ).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state=OrderStateChoices.CREATED)
                except IntegrityError as err:
                    return JsonResponse({'error': str(err)}, status=400)
                if is_updated:
                    new_order.send(sender=self.__class__, user_id=request.user.id)
                    return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=http_status.HTTP_400_BAD_REQUEST)
