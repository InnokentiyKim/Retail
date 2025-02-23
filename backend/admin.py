from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .tasks import export_to_csv
from .models import User, Shop, Category, Product, ProductItem, Order, OrderItem, Contact, EmailTokenConfirm, Coupon


def admin_export_to_csv(modeladmin, request, queryset):
    """
    Этот метод вызывается из административного интерфейса Django и экспортирует выбранные данные в CSV-файл.
    """
    options = modeladmin.model._meta
    export_to_csv.delay(options, queryset)

admin_export_to_csv.short_description = "Export to CSV"


class ContactInline(admin.TabularInline):
    """
    Встраиваемая форма для добавления и редактирования контактов в административном интерфейсе Django.
    """
    model = Contact
    extra = 1

class ProductInline(admin.TabularInline):
    """
    Встраиваемая форма для добавления и редактирования продуктов в административном интерфейсе Django.
    """
    model = Product
    extra = 1

class ProductItemInline(admin.TabularInline):
    """
    Встраиваемая форма для добавления и редактирования экземпляров продуктов в административном интерфейсе Django.
    """
    model = ProductItem
    extra = 1


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Кастомный административный интерфейс для пользователей в Django.
    """
    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('last_login', )
    inlines = [ContactInline]


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для магазинов.
    """
    list_display = ('name', 'user', 'is_active')
    list_filter = ('user', 'is_active')
    search_fields = ('name', 'description')
    inlines = [ProductItemInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для категорий товаров.
    """
    list_display = ('name', )
    list_filter = ('name', 'shops')
    search_fields = ('name', )
    ordering = ('name', )
    raw_id_fields = ('shops', )
    inlines = [ProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для продуктов.
    """
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    ordering = ('name', )
    inlines = [ProductItemInline]


@admin.register(ProductItem)
class ProductItemAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для экземпляров продуктов.
    """
    list_display = ('product', 'shop', 'quantity', 'preview', 'price', 'price_retail')
    list_filter = ('product', 'shop')
    search_fields = ('product__name', 'shop__name')
    ordering_fields = ('product', 'quantity', 'price', 'price_retail')


class OrderItemInline(admin.TabularInline):
    """
    Встраиваемая форма для добавления и редактирования заказов в административном интерфейсе Django.
    """
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для заказов.
    """
    list_display = ('user', 'created_at', 'state', 'contact')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    actions = [admin_export_to_csv]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для скидочных купонов.
    """
    list_display = ('code', 'valid_from', 'valid_to', 'discount', 'active')
    list_filter = ('valid_from', 'valid_to', 'active')
    search_fields = ('code', 'discount')
    date_hierarchy = 'valid_from'


@admin.register(EmailTokenConfirm)
class EmailTokenConfirmAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для токенов подтверждения email.
    """
    list_display = ('user', 'key', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__email', 'user__username')
