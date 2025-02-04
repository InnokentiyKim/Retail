from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from backend.models import User, Shop, Category, Product, ProductItem, Order, OrderItem, Contact, EmailTokenConfirm


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'auth_token')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'description', 'user', 'is_active')
    list_filter = ('user', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category')


@admin.register(ProductItem)
class ProductItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'quantity', 'preview', 'price', 'price_retail')
    list_filter = ('product', 'shop')
    search_fields = ('product', 'shop')
    ordering_fields = ('product', 'quantity', 'price', 'price_retail')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'state', 'contact')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_item', 'quantity')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'country', 'city', 'street', 'house', 'structure', 'building', 'apartment')
    list_filter = ('user', 'country', 'city')
    search_fields = ('user', 'country', 'city', 'street')


@admin.register(EmailTokenConfirm)
class EmailTokenConfirmAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user', )
