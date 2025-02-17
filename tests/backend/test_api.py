import os.path
import pytest
import yaml
from django.urls.base import reverse
from .fixtures import settings, client, user_factory, admin_user_factory, obtain_users_token, orders_factory, \
    order_items_factory, obtain_users_credentials
from backend.models import User, EmailTokenConfirm, UserTypeChoices
from rest_framework import status
from pytest_mock import mocker


@pytest.mark.parametrize(
    ['email', 'username', 'password', 'first_name', 'last_name', 'expected'],
    (
        ('user1@mail.ru', 'user1', 'secret1234', 'test', 'test', status.HTTP_201_CREATED),
        ('user3@mail.ru', 'user3', 'test', 'test', 'test', status.HTTP_400_BAD_REQUEST),
        (None, 'user3', 'secret1234', 'test', 'test', status.HTTP_409_CONFLICT),
        ('user4@mail.ru', None, 'secret1234', 'test', 'test', status.HTTP_409_CONFLICT),
        ('user5@mail.ru', 'user5', None, 'test', 'test', status.HTTP_400_BAD_REQUEST),
        ('user5@mail.ru', 'user5', 'secret1234', None, None, status.HTTP_409_CONFLICT),
    )
)
@pytest.mark.django_db
def test_create_user(client, email, username, password, first_name, last_name, expected):
    url = reverse('backend:user-register')
    payload = {
        'email': email,
        'username': username,
        'password': password,
        'first_name': first_name,
        'last_name': last_name
    }
    count = User.objects.count()
    response = client.post(url, data=payload)
    assert response.status_code == expected
    if expected == status.HTTP_201_CREATED:
        created_user = User.objects.get(email=email)
        assert created_user.username == username
        assert created_user.is_active is False
        assert User.objects.count() == count + 1
        existing_payload = payload.copy()
        existing_payload['username'] = username + '1'
        response = client.post(url, data=existing_payload)
        assert response.status_code == status.HTTP_409_CONFLICT
        existing_payload['username'] = username
        response = client.post(url, data=existing_payload)
        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_confirm_account(client):
    create_user_url = reverse('backend:user-register')
    confirm_url = reverse('backend:user-register-confirm')
    user_payload = {
        'email': 'user1@mail.ru',
        'username': 'user1',
        'password': 'secret1234',
        'first_name': 'test',
        'last_name': 'test'
    }
    response = client.post(create_user_url, data=user_payload)
    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.filter(email=user_payload['email']).first()
    assert user.is_active is False
    confirm_token = EmailTokenConfirm.objects.create(user=user)
    payload = {'email': user.email, 'token': confirm_token.key}
    response = client.post(confirm_url, data=payload)
    assert response.status_code == status.HTTP_200_OK
    user = User.objects.filter(email=user_payload['email']).first()
    assert user.is_active is True

    payload = {'email': None, 'token': confirm_token.key}
    response = client.post(confirm_url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    payload = {'email': user_payload['email'], 'token': None}
    response = client.post(confirm_url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_login(client, user_factory):
    token_obtain_url = reverse('backend:token-obtain-pair')
    token_refresh_url = reverse('backend:token-refresh')
    password = 'secret1234'
    user = user_factory(password=password, _quantity=1)
    payload = {'email': user.email, 'password': password}
    obtain_response = client.post(token_obtain_url, data=payload)
    assert obtain_response.status_code == status.HTTP_200_OK
    assert 'access' in obtain_response.data
    assert 'refresh' in obtain_response.data

    wrong_password = password + '1'
    obtain_response_wrong = client.post(token_obtain_url, data={'email': user.email, 'password': wrong_password})
    assert obtain_response_wrong.status_code == status.HTTP_401_UNAUTHORIZED

    refresh_response = client.post(token_refresh_url, data={'refresh': obtain_response.data['refresh']})
    assert refresh_response.status_code == status.HTTP_200_OK
    assert 'access' in refresh_response.data
    assert obtain_response.data['access'] != refresh_response.data['access']


@pytest.mark.django_db
def test_change_account_info(client, obtain_users_token):
    url = reverse('backend:user-account')
    token = obtain_users_token(user_type=UserTypeChoices.BUYER).get('access')
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    payload = {'email': 'user1@mail.ru', 'username': 'test123', 'first_name': 'test', 'last_name': 'test'}
    response = client.post(url, payload)
    assert response.status_code == status.HTTP_200_OK
    user = User.objects.filter(email=payload['email']).first()
    assert user is not None
    for key, value in payload.items():
        assert getattr(user, key) == value


@pytest.mark.django_db
def test_get_account_info(client, obtain_users_token):
    url = reverse('backend:user-account')
    token = obtain_users_token(user_type=UserTypeChoices.BUYER).get('access')
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None


# @pytest.mark.django_db
# def test_update_seller_goods(client, obtain_users_token, mocker):
#     url = reverse('backend:seller-goods')
#     token = obtain_users_token(user_type=UserTypeChoices.SELLER).get('access')
#     client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
#     file_upload_url = 'https://test.com/test_file.yaml'
#     file_path = os.path.join(os.path.dirname(__file__), 'shops_test_data.yaml')
#     with open(file_path, 'rb') as file:
#         yaml_data = file.read()
#     mocker.patch('requests.get', return_value={'content': yaml_data})
#     response = client.post(url, {'url': file_upload_url})
#     assert response.status_code == status.HTTP_200_OK
#     assert response.data is not None


@pytest.mark.django_db
def test_get_categories(client):
    url = reverse('backend:categories')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_shops(client):
    url = reverse('backend:shops')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_get_product_items(client):
    url = reverse('backend:shops')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


# @pytest.mark.django_db
# def test_shopping_cart(client, obtain_users_token, obtain_users_credentials, orders_factory):
#     url = reverse('backend:shoppingcart')
#     user_email, user_password = 'user@mail.ru', 'secret1234'
#     users_info = obtain_users_credentials(email=user_email, password=user_password)
#     token = users_info['token'].get('access')
#     user_id = users_info.get('user_id')
#     assert user_id is not None
#     client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
#     order = orders_factory(user=user_id, _quantity=1)
#     response = client.get(url)
#     assert response.status_code == status.HTTP_200_OK
#     assert len(response.data) == 1

