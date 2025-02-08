import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api():
    assert 1 == 1