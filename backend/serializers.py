from backend.models import ProductDetails, Contact, Order, OrderItem
from models import User, Shop, Category, Product
from rest_framework import serializers


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'user', 'phone', 'country', 'city', 'street', 'house', 'structure', 'building', 'apartment']
        read_only_fields = ['id']
        extra_kwargs = {
            'user': {'read_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'contacts']
        read_only_fields = ['id']


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'description', 'shop']


class ProductDetailsSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductDetails
        fields = ['id', 'product', 'quantity', 'price', 'price_retail', 'parameters']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'state', 'contact']
        read_only_fields = ['id']


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'quantity']
        read_only_fields = ['id']
        extra_kwargs = {
            'order': {'read_only': True},
        }
