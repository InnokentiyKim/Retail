import pytest
from django.urls.base import reverse
from rest_framework.test import APIClient
from model_bakery import baker

from backend.models import UserTypeChoices


@pytest.fixture(autouse=True)
def settings():
    from django.conf import settings
    settings.DEBUG = True
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
    settings.CASHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    return settings


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_factory():
    def factory(*args, **kwargs):
        model_args = {'is_staff': False, 'is_superuser': False, 'is_active': True, 'type': UserTypeChoices.BUYER}
        if '_quantity' in kwargs and kwargs['_quantity'] == 1:
            if 'email' in kwargs:
                model_args['email'] = kwargs['email']
            if 'type' in kwargs:
                model_args['type'] = kwargs['type']
            user = baker.make('backend.User', **model_args)
            if 'password' in kwargs:
                user.set_password(kwargs['password'])
                user.save()
            return user
        return baker.make('backend.User', **model_args)
    return factory

@pytest.fixture
def admin_user_factory():
    def factory(*args, **kwargs):
        model_args = {'is_staff': True, 'is_superuser': True, 'is_active': True}
        if '_quantity' in kwargs and kwargs['_quantity'] == 1:
            admin_user = baker.make('backend.User', **model_args)
            if 'password' in kwargs:
                admin_user.set_password(kwargs['password'])
                admin_user.save()
            return admin_user
        return baker.make('backend.User', **model_args)
    return factory


@pytest.fixture
def obtain_users_token(user_factory, password='secret1234', user_type=UserTypeChoices.BUYER):
    def factory(*args, **kwargs):
        url = reverse('backend:token-obtain-pair')
        user = user_factory(password=password, type=user_type, _quantity=1)
        payload = {'email': user.email, 'password': password}
        response = APIClient().post(url, data=payload)
        return response.data
    return factory


@pytest.fixture
def obtain_users_credentials(user_factory, email='user@mail.ru', password='secret1234', user_type=UserTypeChoices.BUYER):
    def factory(*args, **kwargs):
        url = reverse('backend:token-obtain-pair')
        user = user_factory(email=email, password=password, type=user_type, _quantity=1)
        payload = {'email': user.email, 'password': password}
        response = APIClient().post(url, data=payload)
        result = {'user_id': user.id, 'token': response.data}
        return result
    return factory


@pytest.fixture
def order_items_factory(user_factory):
    def factory(*args, **kwargs):
        user = user_factory(type=UserTypeChoices.SELLER, _quantity=1)
        shop = baker.make('Shop', user=user, _quantity=1)
        products = baker.make('Product', _quantity=5)
        product_items = [baker.make('ProductItem', shop=shop, product=product) for product in products]
        order_items = []
        for product_item in product_items:
            order_items = baker.make('OrderItem', product_item=product_item, _quantity=5)
        return order_items
    return factory


@pytest.fixture
def orders_factory(user_id=None):
    def factory(*args, **kwargs):
        shop = baker.make('Shop', user_id=user_id, _quantity=1)[0]
        # category = baker.make('Category', shops=shop, _quantity=1)
        products = baker.make('Product', _quantity=5)
        product_items = [baker.make('ProductItem', shop=shop, product=product) for product in products]
        order = baker.make('Order', user_id=user_id, _quantity=1)[0]
        for product_item in product_items:
            baker.make('OrderItem', order=order, product_item=product_item)
        return order
    return factory
