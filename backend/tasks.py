import csv
import yaml
import datetime
import requests
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import status as http_status

from backend.models import Shop, Category, Product, ProductItem, Property, ProductProperty
from backend.serializers import ShopGoodsImportSerializer


@shared_task
def send_email(subject: str, message: str, from_email: str, to_email: list[str]):
    msg = EmailMultiAlternatives(subject, message, from_email, to_email)
    msg.send()


@shared_task
def import_goods(request, *args, **kwargs):
    url = request.data.get('url', None)
    if url is None:
        return JsonResponse({'error': 'url is required'}, status=http_status.HTTP_400_BAD_REQUEST)
    validate_url = URLValidator()
    try:
        validate_url(url)
    except ValidationError as error:
        return JsonResponse({'status': False, 'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
    stream = requests.get(url).content
    data = yaml.safe_load(stream)
    serializer = ShopGoodsImportSerializer(data=data)
    if serializer.is_valid():
        valid_data = serializer.validated_data
    else:
        return JsonResponse({'status': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
    shop, _ = Shop.objects.get_or_create(name=valid_data['shop'], user_id=request.user.id)
    for category in valid_data['categories']:
        product_category, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        product_category.shops.add(shop)
        product_category.save()
    for item in valid_data['goods']:
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


@shared_task
def export_to_csv(modeladmin, request, queryset):
    options = modeladmin.model._meta
    content_disposition = f"attachment; filename={options.verbose_name}.csv"
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)
    fields = [field for field in options.get_fields() if not field.many_to_many and not field.one_to_many]
    writer.writerow([field.verbose_name for field in fields])
    for item in queryset:
        data_row = []
        for field in fields:
            value = getattr(item, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d")
            data_row.append(value)
        writer.writerow(data_row)
    return response
