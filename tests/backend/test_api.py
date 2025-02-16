import pytest
from django.urls.base import reverse
from rest_framework.test import APIClient
from model_bakery import baker
from backend.models import User, EmailTokenConfirm
from rest_framework import status


@pytest.fixture(autouse=True)
def settings():
    from django.conf import settings
    settings.DEBUG = True
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
    return settings


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user('test', 'test')


@pytest.fixture
def users_factory():
    def factory(*args, **kwargs):
        return baker.make('User', *args, **kwargs)
    return factory


@pytest.fixture
def orders_factory():
    def factory(*args, **kwargs):
        return baker.make('Order', *args, **kwargs)
    return factory


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
def test_confirm_account(client, user):
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

