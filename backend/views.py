import json

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Sum, F, Q
from django.shortcuts import render
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from .models import User, Shop, Category, Product, ProductDetails, Order, OrderStateChoices, OrderItem, UserTypeChoices, \
    Contact
import yaml

from .serializers import CategorySerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, \
    ProductDetailsSerializer, ContactSerializer


class ShopGoodsView(APIView):
    def post(self, request: Request, *args, **kwargs):
        url = request.data.get('url', None)
        if url is None:
            return JsonResponse({'error': 'url is required'}, status=400)
        validate_url = URLValidator(verify_exists=True)
        try:
            validate_url(url)
        except ValidationError:
            return JsonResponse({'error': 'url is invalid'}, status=400)
        stream = get(url).content
        data = yaml.safe_load(stream)
        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
        for category in data['categories']:
            product_category, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        for item in data['goods']:
            product, created = Product.objects.get_or_create(name=item['name'], category_id=item['category_id'], shop_id=shop.id)
            if not created:
                ProductDetails.objects.filter(product_id=product.id).delete()
            product_details = ProductDetails.objects.create(
                product_id=product.id,
                price=item['price'],
                price_retail=item['price_retail'],
                quantity=item['quantity'],
                parameters=item['parameters'],
            )
        return JsonResponse({'Status': True}, status=200)


class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    queryset = Shop.objects.filter(is_active=True)
    serializer_class = ShopSerializer


class ProductDetailsView(APIView):
    def get(self, request: Request, *args, **kwargs):
        query = Q(shop__is_active=True)
        shop_id = request.query_params.get('shop_id', None)
        category_id = request.query_params.get('category_id', None)
        if shop_id:
            query &= Q(shop__id=shop_id)
        if category_id:
            query &= Q(product__category_id=category_id)
        queryset = ProductDetails.objects.filter(query).select_related(
            'product__shop', 'product__category').distinct()
        serializer = ProductDetailsSerializer(queryset, many=True)
        return Response(serializer.data)


class ShoppingCartView(APIView):
    def get(self, request: Request, *args, **kwargs):
        cart = Order.objects.filter(
            user_id=request.user.id).prefetch_related(
            'ordered_items__product__category').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('order_items__product__details__price'))).distinct()
        serializer = OrderSerializer(cart, many=True)
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs):
        updating_items = request.data.get('items')
        if updating_items is None:
            return JsonResponse({'error': 'items is required'}, status=400)
        try:
            updating_items_dict = json.loads(updating_items)
        except ValueError:
            return JsonResponse({'error': 'items format is invalid'}, status=400)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.gathering)
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

    def put(self, request: Request, *args, **kwargs):
        adding_items = request.data.get('items')
        if adding_items:
            try:
                adding_items_dict = json.loads(adding_items)
            except ValueError:
                return JsonResponse({'error': 'items format is invalid'}, status=400)
            cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.gathering)
            for item in adding_items_dict:
                if type(item['id']) is int and type(item['quantity']) is int:
                    OrderItem.objects.filter(order_id=cart.id, id=item['id']).update(quantity=item['quantity'])
            return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=400)

    def delete(self, request: Request, *args, **kwargs):
        deleting_items = request.data.get('items')
        if deleting_items:
            deleting_items_list = deleting_items.split(',')
            cart = get_object_or_404(Order, user_id=request.user.id, state=OrderStateChoices.gathering)
            query = Q()
            has_deleting_items = False
            for item_id in deleting_items_list:
                if item_id.isdigit():
                    query |= Q(order_id=cart.id, id=item_id)
                    has_deleting_items = True
            if has_deleting_items:
                OrderItem.objects.filter(query).delete()
                return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=400)


class SellerStatusView(APIView):
    def get(self, request: Request, *args, **kwargs):
        if request.user.type != UserTypeChoices.seller:
            return JsonResponse({'error': 'Only sellers are allowed'}, status=403)
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs):
        if request.user.type != UserTypeChoices.seller:
            return JsonResponse({'error': 'Only sellers are allowed'}, status=403)
        status = request.data.get('is_active')
        if status:
            try:
                Shop.objects.filter(user_id=request.user.id).update(is_active=bool(status))
                return JsonResponse({'Status': True}, status=200)
            except IntegrityError as err:
                return JsonResponse({'error': str(err)}, status=400)
            except ValueError as error:
                return JsonResponse({'error': str(error)}, status=400)
        return JsonResponse({'Status': False}, status=400)


class SellerOrdersView(APIView):
    def get(self, request: Request, *args, **kwargs):
        if request.user.type != UserTypeChoices.seller:
            return JsonResponse({'error': 'Only sellers are allowed'}, status=403)
        order = Order.objects.filter(
            ordered_items__product__shop__user_id=request.user.id).exclude(
            state=OrderStateChoices.gathering).prefetch_related(
            'ordered_items__product__category',
            'ordered_items__product__details__parameters').select_related(
            'contact').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('order_items__product__details__price'))
        ).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class ContactView(APIView):
    def get(self, request: Request, *args, **kwargs):
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs):
        if {'city', 'street', 'phone'}.issubset(request.data):
            contact_data = request.data.copy()
            contact_data.update({'user': request.user.id})
            serializer = ContactSerializer(data=contact_data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True}, status=200)
            return JsonResponse({'error': serializer.errors}, status=400)
        return JsonResponse({'Status': False}, status=400)

    def put(self, request: Request, *args, **kwargs):
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

    def delete(self, request: Request, *args, **kwargs):
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
    def get(self, request: Request, *args, **kwargs):
        order = Order.objects.filter(user_id=request.user.id).exclude(state=OrderStateChoices.gathering).prefetch_related(
            'ordered_items__product__category',
            'ordered_items__product__details__parameters').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('order_items__product__details__price'))
        ).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs):
        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state=OrderStateChoices.new)
                except IntegrityError as err:
                    return JsonResponse({'error': str(err)}, status=400)
                if is_updated:
                    # new_order.send(sender=self.__class__, user_id=request.user.id)
                    return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=400)
