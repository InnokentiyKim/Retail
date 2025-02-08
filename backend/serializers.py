from backend.models import ProductItem, Contact, Order, OrderItem, Property, ProductProperty
from backend.models import User, Shop, Category, Product
from rest_framework import serializers


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'phone', 'country', 'city', 'street', 'house', 'apartment']
        read_only_fields = ['id']
        extra_kwargs = {
            'user': {'read_only': True},
            'structure': {'required': False},
            'building': {'required': False},
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
        fields = ['id', 'name', 'url', 'description', 'is_active']
        read_only_fields = ['id']
        not_required_fields = ['url', 'description', 'is_active']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'category']
        read_only_fields = ['id']


class PropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductPropertySerializer(serializers.ModelSerializer):
    property = serializers.StringRelatedField()

    class Meta:
        model = ProductProperty
        fields = ['property', 'value']


class ProductItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_properties = ProductPropertySerializer(many=True, read_only=True)

    class Meta:
        model = ProductItem
        fields = ['id', 'product', 'shop', 'quantity', 'preview', 'price', 'price_retail', 'product_properties']
        read_only_fields = ['id']
        not_required_fields = ['preview']


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product_item', 'quantity']
        read_only_fields = ['id']
        extra_kwargs = {
            'order': {'write_only': True},
        }


class OrderItemCreateSerializer(OrderItemSerializer):
    product_item = ProductItemSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(many=True, read_only=True)
    contact = ContactSerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'ordered_items', 'created_at', 'state', 'contact', 'total_price']
        read_only_fields = ['id']
