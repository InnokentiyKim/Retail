from dataclasses import fields

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
import uuid

from rest_framework.exceptions import ValidationError


class OrderStateChoices(models.IntegerChoices):
    PREPARING = 1, "Подготавливается"
    CREATED = 2, "Создан"
    CONFIRMED = 3, "Подтвержден"
    ASSEMBLED = 4, "Собран"
    SENT = 5, "Отправлен"
    DELIVERED = 6, "Доставлен"
    CANCELED = 7, "Отменен"


class UserTypeChoices(models.TextChoices):
    SELLER = "SL", "Seller"
    BUYER = "BR", "Buyer"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    type = models.TextField(verbose_name='Тип пользователя', choices=UserTypeChoices.choices, max_length=2, default=UserTypeChoices.BUYER)
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=False)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        max_length=80,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        }
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username}) - {self.type}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Shop(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=100, verbose_name='Название магазина')
    url = models.URLField(max_length=300, blank=True, null=True, verbose_name='Ссылка на файл продуктов магазина')
    description = models.TextField(blank=True, null=True, verbose_name='Описание магазина')
    user = models.OneToOneField(User, blank=True, on_delete=models.CASCADE, related_name='shop', verbose_name='Пользователь')
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ['-name']
        indexes = [
            models.Index(fields=['-name']),
        ]


class Category(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=80, verbose_name='Название категории')
    shops = models.ManyToManyField(Shop, blank=True, related_name='categories', verbose_name='Магазины')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ['-name']
        indexes = [
            models.Index(fields=['-name']),
        ]


class Product(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=100, verbose_name='Название продукта')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ['-name']
        indexes = [
            models.Index(fields=['-name']),
        ]


class ProductItem(models.Model):
    objects = models.manager.Manager()

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_items', verbose_name='Продукт')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='product_items', verbose_name='Магазин')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10000)],
                                           verbose_name='Количество')
    preview = models.ImageField(upload_to="images/%Y/%m/%d", blank=True, null=True,
                                verbose_name='Превью')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена продукта')
    price_retail = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                       verbose_name='Розничная цена продукта')

    class Meta:
        verbose_name = 'Описание продукта'
        verbose_name_plural = 'Список описаний продуктов'

    def __str__(self):
        return f"{self.product.name}"


class Property(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=100, verbose_name='Название свойства')

    class Meta:
        verbose_name = 'Свойство'
        verbose_name_plural = 'Список свойств'
        ordering = ['-name']

    def __str__(self):
        return self.name


class ProductProperty(models.Model):
    objects = models.manager.Manager()

    product_item = models.ForeignKey(ProductItem, blank=True, on_delete=models.CASCADE,
                                        related_name='product_properties')
    property = models.ForeignKey(Property, blank=True, on_delete=models.CASCADE, related_name='product_properties')
    value = models.CharField(max_length=100, verbose_name='Значение свойства')

    class Meta:
        verbose_name = 'Свойства продукта'
        verbose_name_plural = 'Список  свойств продукта'
        constraints = [models.UniqueConstraint(fields=['product_item', 'property'],
                                               name='unique_product_properties')]

    def __str__(self):
        return f"{self.property.name}"


class Contact(models.Model):
    objects = models.manager.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts', blank=True, null=True,
                             verbose_name='Пользователь')
    phone  = models.CharField(max_length=20, blank=True, verbose_name='Номер телефона')
    country = models.CharField(max_length=30, blank=True, null=True, verbose_name='Страна')
    city = models.CharField(max_length=50, blank=True, verbose_name='Город')
    street = models.CharField(max_length=60, blank=True, verbose_name='Улица')
    house = models.CharField(max_length=20, blank=True, verbose_name='Номер дома')
    structure = models.CharField(max_length=20, blank=True, null=True, verbose_name='Корпус')
    building = models.CharField(max_length=20, blank=True, null=True, verbose_name='Строение')
    apartment = models.CharField(max_length=20, blank=True, verbose_name='Квартира')

    def __str__(self):
        return f"{self.user.email} - {self.phone}"

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов пользователей'


class Order(models.Model):
    objects = models.manager.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания заказа')
    state = models.IntegerField(choices=OrderStateChoices.choices, default=OrderStateChoices.PREPARING,
                                verbose_name='Состояние заказа')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True, related_name='orders',
                                verbose_name='Контакт')

    def __str__(self):
        return f"{self.created_at} - {self.state}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ['-created_at']

    @property
    def total_price(self):
        return sum(item.get_cost() for item in self.ordered_items.all())


class OrderItem(models.Model):
    objects = models.manager.Manager()

    order = models.ForeignKey(Order, blank=True, on_delete=models.CASCADE, related_name='ordered_items', verbose_name='Заказ')
    product_item = models.ForeignKey(ProductItem, blank=True, on_delete=models.CASCADE, related_name='ordered_items',
                                     verbose_name='Экземпляр продукта')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Список позиций заказа'
        constraints = [
            models.UniqueConstraint(fields=['order', 'product_item'], name='unique_order_item')
        ]

    def get_cost(self):
        return self.quantity * self.product_item.price

    def __str__(self):
        return f"{self.product_item.product.name}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='Код купона')
    valid_from = models.DateTimeField(verbose_name='Дата начала действия купона')
    valid_to = models.DateTimeField(verbose_name='Дата окончания действия купона')
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   verbose_name='Скидка', help_text='В процентах от 0 до 100')
    active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Купон'
        verbose_name_plural = 'Список купонов'

    def __str__(self):
        return self.code


class CategoryCoupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='Код купона')
    valid_from = models.DateTimeField(verbose_name='Дата начала действия купона')
    valid_to = models.DateTimeField(verbose_name='Дата окончания действия купона')
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   verbose_name='Скидка', help_text='В процентах от 0 до 100')
    active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания купона')
    categories = models.ManyToManyField(Category, related_name='category_coupons', verbose_name='Категории')

    class Meta:
        verbose_name = 'Купон для категории товаров'
        verbose_name_plural = 'Список купонов для категорий товаров'

    def save(self, *args, **kwargs):
        if ProductCoupon.objects.filter(code=self.code).exists():
            raise ValidationError("Купон с таким кодом уже существует")
        return super(CategoryCoupon, self).save(*args, **kwargs)

    def __str__(self):
        return self.code


class ProductCoupon(models.Model):
    code = models.CharField(max_length=50, unique=True, null=False, verbose_name='Код купона')
    valid_from = models.DateTimeField(verbose_name='Дата начала действия купона')
    valid_to = models.DateTimeField(verbose_name='Дата окончания действия купона')
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   verbose_name='Скидка', help_text='В процентах от 0 до 100')
    active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания купона')
    product_items = models.ManyToManyField(ProductItem, related_name='product_coupons', verbose_name='Продукты')

    class Meta:
        verbose_name = 'Купон для товаров'
        verbose_name_plural = 'Список купонов для товаров'

    def save(self, *args, **kwargs):
        if CategoryCoupon.objects.filter(code=self.code).exists():
            raise ValidationError("Купон с таким кодом уже существует")
        return super(ProductCoupon, self).save(*args, **kwargs)

    def __str__(self):
        return self.code


class EmailTokenConfirm(models.Model):
    objects = models.manager.Manager()

    class Meta:
        verbose_name = 'Токен для подтверждения email'
        verbose_name_plural = 'Токены для подтверждения email'

    @staticmethod
    def generate_token():
        return uuid.uuid4().hex

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confirm_email_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=80, db_index=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_token()
        return super(EmailTokenConfirm, self).save(*args, **kwargs)

    def __str__(self):
        return f"Password reset token for {self.user}"

