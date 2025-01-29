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
from .models import User, Shop, Category, Product, ProductDetails, Order, OrderStateChoices, OrderItem, UserTypeChoices
import yaml

from .serializers import CategorySerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, \
    ProductDetailsSerializer


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


class OrderView(APIView):
    def get(self, request: Request, *args, **kwargs):
        order = Order.objects.filter(
            user_id=request.user.id).prefetch_related(
            'ordered_items__product__category').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('order_items__product__details__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs):
        updating_items = request.data.get('items')
        if updating_items is None:
            return JsonResponse({'error': 'items is required'}, status=400)
        try:
            updating_items_dict = json.loads(updating_items)
        except ValueError:
            return JsonResponse({'error': 'items format is invalid'}, status=400)
        order, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.gathering)
        for item in updating_items_dict:
            item.update({'order_id': order.id})
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
            order, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.gathering)
            for item in adding_items_dict:
                if type(item['id']) is int and type(item['quantity']) is int:
                    OrderItem.objects.filter(order_id=order.id, id=item['id']).update(quantity=item['quantity'])
            return JsonResponse({'Status': True}, status=200)
        return JsonResponse({'Status': False}, status=400)

    def delete(self, request: Request, *args, **kwargs):
        deleting_items = request.data.get('items')
        if deleting_items:
            deleting_items_list = deleting_items.split(',')
            order = get_object_or_404(Order, user_id=request.user.id, state=OrderStateChoices.gathering)
            query = Q()
            has_deleting_items = False
            for item_id in deleting_items_list:
                if item_id.isdigit():
                    query |= Q(order_id=order.id, id=item_id)
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
        pass










