import os.path
import requests
from email.mime.application import MIMEApplication
from typing import Any
from django.db import IntegrityError
import yaml
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from backend.models import Category, Product, ProductItem, Property, ProductProperty
from backend.serializers import ShopGoodsImportSerializer


@shared_task
def send_email(subject: str, message: str, from_email: str, to_email: list[str], attached_file: bytes|Any=None):
    """
    Задача Celery для отправки письма по email

    Параметры:
        - subject (str): Тема письма
        - message (str): Текст сообщения
        - from_email (str): Адрес отправителя
        - to_email (list[str]): Список адресов получателей
        - attachment (bytes|Any): Файл вложения (байтовый массив)
    """
    msg = EmailMultiAlternatives(subject=subject, body=message, from_email=from_email, to=to_email)
    if attached_file is not None:
        attachments = MIMEApplication(attached_file, 'pdf')
        attachments.add_header('Content-Disposition', 'attachment', filename='report.pdf')
        msg.attachments = [attachments]
    msg.send()


@shared_task
def import_goods(url: str, shop_id: int, user_id: int):
    """
    Задача Celery для импорта товаров из YAML-файла

    Параметры:
        - url (str): URL YAML-файла
        - user_id (int): Идентификатор пользователя
    """
    # stream = requests.get(url).content
    path = os.path.join(os.path.dirname(__file__), 'shops_data.yaml')
    with open(path, 'rb') as file:
        stream = file.read()
    try:
        data = yaml.safe_load(stream)
    except Exception as err:
        return {'success': False, 'error': str(err)}
    serializer = ShopGoodsImportSerializer(data=data)
    if serializer.is_valid():
        valid_data = serializer.validated_data
    else:
        return {'success': False, 'error': serializer.errors}
    for category in valid_data['categories']:
        try:
            product_category = Category.objects.filter(id=category['id']).first()
            if not product_category:
                product_category = Category.objects.create(name=category['name'])
            product_category.shops.add(shop_id)
            product_category.save()
        except IntegrityError as err:
            return {'success': False, 'error': str(err)}
    for item in valid_data['goods']:
        try:
            product, created = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
            product_item = ProductItem.objects.create(
                product_id=product.id,
                article_id=item['article_id'],
                shop_id=shop_id,
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
        except IntegrityError as err:
            return {'success': False, 'error': str(err)}
    return {'success': True}
