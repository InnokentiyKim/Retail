import random
import pytest
from django.urls.base import reverse
from rest_framework.test import APIClient
from model_bakery import baker
from backend.models import UserTypeChoices


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
        return baker.make('backend.User', **model_args, _quantity=kwargs['_quantity'])
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
        url = reverse('backend:token-obtain')
        user = user_factory(password=password, type=user_type, _quantity=1)
        payload = {'email': user.email, 'password': password}
        response = APIClient().post(url, data=payload)
        return response.data
    return factory


@pytest.fixture
def obtain_users_credentials(user_factory, email='user@mail.ru', password='secret1234', user_type=UserTypeChoices.BUYER):
    def factory(email=email, password=password, user_type=user_type):
        url = reverse('backend:token-obtain')
        user = user_factory(email=email, password=password, type=user_type, _quantity=1)
        payload = {'email': user.email, 'password': password}
        response = APIClient().post(url, data=payload)
        result = {'user_id': user.id, 'token': response.data}
        return result
    return factory


@pytest.fixture
def make_shops_with_products_factory(user_factory):
    def factory(*args, **kwargs):
        sellers = user_factory(type=UserTypeChoices.SELLER, _quantity=10)
        shops = []
        for seller in sellers:
            shops = baker.make('Shop', user=seller, is_active=True, _quantity=1)
        categories = baker.make('Category', shops=shops, _quantity=10)
        products = baker.make('Product', category=random.choice(categories), _quantity=10)
        product_items = []
        for shop in shops:
            for product in products:
                product_items.append(baker.make('ProductItem', shop=shop, product=product, quantity=10))
        return product_items
    return factory
