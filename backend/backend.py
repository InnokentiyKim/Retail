import json
import yaml
import requests
from django.contrib.auth.password_validation import validate_password
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import F, Q
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from .models import EmailTokenConfirm, Shop, Category, Product, ProductItem, Property, ProductProperty, Order, \
    OrderStateChoices, OrderItem, Contact
from .serializers import UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, ContactSerializer, \
    ProductItemSerializer
from rest_framework import status as http_status
from rest_framework.authtoken.models import Token


class UserBackend:
    @staticmethod
    def register_account(request: Request):
        if {'email', 'username', 'first_name', 'last_name', 'password'}.issubset(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'status': True}, status=http_status.HTTP_201_CREATED)
                else:
                    return JsonResponse({'status': False, 'errors': user_serializer.errors},
                                        status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': False, }, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def confirm_account(request):
        if {'email', 'token'}.issubset(request.data):
            token = EmailTokenConfirm.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'status': True}, status=http_status.HTTP_200_OK)
            else:
                return JsonResponse({'status': False, 'error': 'Неверно указан email или токен'},
                                    status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def login_account(request):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user and user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return JsonResponse({'status': True, 'token': token.key}, status=http_status.HTTP_200_OK)
            return JsonResponse({'status': False, 'error': 'Authentication failed'},
                                status=http_status.HTTP_403_FORBIDDEN)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_account_info(request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @staticmethod
    def change_account_info(request):
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
            else:
                request.user.set_password(request.data['password'])
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True}, status=http_status.HTTP_200_OK)
        else:
            return JsonResponse({'Status': False, 'errors': user_serializer.errors},
                                status=http_status.HTTP_400_BAD_REQUEST)


class SellerBackend:
    @staticmethod
    def update_goods(request):
        url = request.data.get('url', None)
        if url is None:
            return JsonResponse({'status': False, 'error': 'url is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        validate_url = URLValidator(verify_exists=True)
        try:
            validate_url(url)
        except ValidationError as error:
            return JsonResponse({'status': False, 'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
        stream = requests.get(url).content
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
        return JsonResponse({'status': True}, status=http_status.HTTP_200_OK)

    @staticmethod
    def get_status(request):
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    @staticmethod
    def change_status(request):
        seller_status = request.data.get('is_active')
        if seller_status is not None:
            try:
                Shop.objects.filter(user_id=request.user.id).update(is_active=bool(seller_status))
                return JsonResponse({'status': True}, status=http_status.HTTP_200_OK)
            except IntegrityError as db_err:
                return JsonResponse({'status': False,'error': str(db_err)}, status=http_status.HTTP_400_BAD_REQUEST)
            except ValueError as val_err:
                return JsonResponse({'status': False, 'error': str(val_err)}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_orders(request):
        orders = Order.objects.filter(
            ordered_items__product_item__shop__user_id=request.user.id).exclude(
            state=OrderStateChoices.PREPARING).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties').select_related(
            'contact').annotate(F('total_price')).distinct()
        # total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product_item__price'))
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class BuyerBackend:
    @staticmethod
    def get_shopping_cart(request):
        cart = Order.objects.filter(
            user_id=request.user.id).prefetch_related(
            'ordered_items__product__category').annotate(
            total_price=F('total_price')).distinct()
        serializer = OrderSerializer(cart, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_update_shopping_cart(request):
        updating_items = request.data.get('items')
        if updating_items is None:
            return JsonResponse({'status': False, 'error': 'items is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        try:
            updating_items_dict = json.loads(updating_items)
        except ValueError:
            return JsonResponse({'status': False, 'error': 'items format is invalid'}, status=http_status.HTTP_400_BAD_REQUEST)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.PREPARING)
        for item in updating_items_dict:
            item.update({'order_id': cart.id})
            serializer = OrderItemSerializer(item)
            if serializer.is_valid():
                try:
                    serializer.save()
                except IntegrityError as err:
                    return JsonResponse({'status': False, 'error': str(err)}, status=http_status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({'status': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': True}, status=http_status.HTTP_200_OK)

    @staticmethod
    def update_shopping_cart(request):
        adding_items = request.data.get('items')
        if adding_items:
            try:
                adding_items_dict = json.loads(adding_items)
            except ValueError:
                return JsonResponse({'error': 'items format is invalid'}, status=http_status.HTTP_400_BAD_REQUEST)
            cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.CREATED)
            for item in adding_items_dict:
                if type(item['id']) is int and type(item['quantity']) is int:
                    OrderItem.objects.filter(order_id=cart.id, id=item['id']).update(quantity=item['quantity'])
            return JsonResponse({'status': True}, status=http_status.HTTP_200_OK)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete_shopping_cart_items(request):
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
                    return JsonResponse({'Status': True}, status=http_status.HTTP_204_NO_CONTENT)
        return JsonResponse({'Status': False}, status=http_status.HTTP_400_BAD_REQUEST)


class ContactBackend:
    @staticmethod
    def get_contact(request):
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_contact(request):
        if {'city', 'street', 'house', 'apartment', 'phone'}.issubset(request.data):
            contact_data = request.data.copy()
            contact_data.update({'user': request.user.id})
            serializer = ContactSerializer(data=contact_data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'status': True}, status=http_status.HTTP_201_CREATED)
            return JsonResponse({'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update_contact(request):
        if 'id' in request.data and request.data['id'].isdigit():
            contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
            if contact:
                serializer = ContactSerializer(contact, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'status': True}, status=http_status.HTTP_200_OK)
                else:
                    return JsonResponse({'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete_contact(request):
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
                return JsonResponse({'status': True}, status=http_status.HTTP_204_NO_CONTENT)
        return JsonResponse({'status': False}, status=http_status.HTTP_400_BAD_REQUEST)


class ProductsBackend:
    @staticmethod
    def get_products(request):
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
