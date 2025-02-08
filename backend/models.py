from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
import uuid


class OrderStateChoices(models.IntegerChoices):
    NEW = 1, "Новый"
    GATHERING = 2, "Подготавливается"
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

    type = models.TextField(choices=UserTypeChoices.choices, max_length=2, default=UserTypeChoices.BUYER)
    email = models.EmailField(unique=True)
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

    name = models.CharField(max_length=100)
    url = models.URLField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    user = models.OneToOneField(User, blank=True, on_delete=models.CASCADE, related_name='shop')
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ['-name']


class Category(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=80)
    shops = models.ManyToManyField(Shop, blank=True, related_name='categories')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ['-name']


class Product(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ['-name']


class ProductItem(models.Model):
    objects = models.manager.Manager()

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='product_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10000)])
    preview = models.ImageField(upload_to='images/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_retail = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = 'Описание продукта'
        verbose_name_plural = 'Список описаний продуктов'


class Property(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(max_length=100)

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
    value = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Свойства продукта'
        verbose_name_plural = 'Список  свойств продукта'
        constraints = [models.UniqueConstraint(fields=['product_item', 'property'],
                                               name='unique_product_properties')]


class Contact(models.Model):
    objects = models.manager.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts', blank=True, null=True)
    phone  = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=30, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    street = models.CharField(max_length=60, blank=True)
    house = models.CharField(max_length=20, blank=True)
    structure = models.CharField(max_length=20, blank=True, null=True)
    building = models.CharField(max_length=20, blank=True, null=True)
    apartment = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}, {self.apartment}. Phone number is {self.phone}"

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов пользователя'


class Order(models.Model):
    objects = models.manager.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.IntegerField(choices=OrderStateChoices.choices, default=OrderStateChoices.NEW)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True, related_name='orders')

    def __str__(self):
        return f"{self.created_at} - {self.state}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ['-created_at']


class OrderItem(models.Model):
    objects = models.manager.Manager()

    order = models.ForeignKey(Order, blank=True, on_delete=models.CASCADE, related_name='ordered_items')
    product_item = models.ForeignKey(ProductItem, blank=True, on_delete=models.CASCADE, related_name='ordered_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Список позиций заказа'
        constraints = [
            models.UniqueConstraint(fields=['order', 'product_item'], name='unique_order_item')
        ]


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

