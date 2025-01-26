from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Q
from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from .models import User, Shop, Category, Product, ProductDetails, Order
import yaml

from .serializers import CategorySerializer, ShopSerializer, OrderSerializer


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


class OrderView(APIView):
    def get(self, request: Request, *args, **kwargs):
        order = Order.objects.filter(
            user_id=request.user.id).prefetch_related(
            'ordered_items__product__category').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('order_items__product__details__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs):
        pass
