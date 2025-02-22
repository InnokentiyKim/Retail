from django.utils import timezone
from backend.models import ProductItem, Contact, Order, OrderItem, Property, ProductProperty, OrderStateChoices
from backend.models import User, Shop, Category, Product, Coupon
from rest_framework import serializers


class ObjectIDSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, allow_null=False)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'user', 'phone', 'country', 'city', 'street', 'house', 'apartment', 'structure', 'building']
        read_only_fields = ['id']
        extra_kwargs = {
            'user': {'write_only': True},
            'country': {'required': False},
            'structure': {'required': False},
            'building': {'required': False},
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'type', 'contacts']
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


class OrderItemUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, allow_null=False)
    quantity = serializers.IntegerField(min_value=1, max_value=10000, allow_null=False)


class OrderItemCreateUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, allow_null=False)
    quantity = serializers.IntegerField(min_value=1, max_value=10000, allow_null=False)
    product_item = serializers.IntegerField(min_value=0, allow_null=False)


class OrderItemDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, allow_null=False)


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


class OrderStateSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, allow_null=False)
    state = serializers.ChoiceField(choices=OrderStateChoices.choices)


class OrderConfirmSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0, allow_null=False)
    contact = serializers.IntegerField(min_value=0, allow_null=False)
    coupon_code = serializers.CharField(max_length=60, required=False, allow_null=True)


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'valid_from', 'valid_to', 'discount', 'active']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['valid_from'] > attrs['valid_to']:
            raise serializers.ValidationError("Дата начала скидки не может быть позже даты окончания действия купона")
        if attrs['valid_from'] < timezone.now():
            raise serializers.ValidationError("Дата начала скидки не может быть раньше текущей даты")
        if attrs['valid_to'] < timezone.now():
            raise serializers.ValidationError("Дата окончания действия купона не может быть раньше текущей даты")
        if attrs['discount'] < 0 or attrs['discount'] > 100:
            raise serializers.ValidationError("Скидка не может быть ниже 0 или превышать 100")
        return attrs



class ShopCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class ShopProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    category = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_retail = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    properties = serializers.DictField()

    def validate_category(self, value):
        if value < 0:
            raise serializers.ValidationError("Категорией может быть только положительное число")
        return value

    def validate_price(self, value):
        if value < 0 or value > 100000000:
            raise serializers.ValidationError("Цена не может быть ниже 0 или превышать 10 000 000")
        return value

    def validate_price_retail(self, value):
        if value < 0.0 or value > 100000000:
            raise serializers.ValidationError("Розничная цена не может быть ниже 0 или превышать 10 000 000")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть больше 0")
        return value


class ShopGoodsImportSerializer(serializers.Serializer):
    categories = ShopCategorySerializer(many=True)
    goods = ShopProductSerializer(many=True)
