from rest_framework import permissions
from backend.models import UserTypeChoices


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.type == UserTypeChoices.SELLER:
            return True
        return False


class IsBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.type == UserTypeChoices.BUYER:
            return True
        return False