from rest_framework import permissions
from backend.models import UserTypeChoices


class IsSeller(permissions.BasePermission):
    """
    Класс разрешений для проверки является ли пользователь продавцом
    """
    def has_permission(self, request, view):
        if request.user and request.user.type == UserTypeChoices.SELLER:
            return True
        return False


class IsBuyer(permissions.BasePermission):
    """
    Класс разрешений для проверки является ли пользователь покупателем
    """
    def has_permission(self, request, view):
        if request.user and request.user.type == UserTypeChoices.BUYER:
            return True
        return False