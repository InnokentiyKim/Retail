from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
import uuid


class OrderStateChoices(models.TextChoices):
    """
    Состояния заказа
    """
    PREPARING = "PREPARING", "Подготавливается"
    CREATED = "CREATED", "Создан"
    CONFIRMED = "CONFIRMED", "Подтвержден"
    ASSEMBLED = "ASSEMBLED", "Собран"
    SENT = "SENT", "Отправлен"
    DELIVERED = "DELIVERED", "Доставлен"
    CANCELED = "CANCELED", "Отменен"


class UserTypeChoices(models.TextChoices):
    """
    Тип пользователя
    """
    SELLER = "SL", "Seller"
    BUYER = "BR", "Buyer"


class UserManager(BaseUserManager):
    """
    Менеджер для модели User
    """
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
    """
    Модель пользователя
    Поля:
        - type (UserTypeChoices): Тип пользователя
        - email (str): Почта пользователя
        - is_active (bool): Пользователь активен
        - username (str): Имя пользователя
    """
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    type = models.TextField(verbose_name='Тип пользователя', choices=UserTypeChoices.choices,
                            max_length=2, default=UserTypeChoices.BUYER)
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=False)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        max_length=80,
        unique=True,
        db_index=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        }
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.type}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class Profile(models.Model):
    objects = UserManager()

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='images/users/%Y/%m/%d', blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.email}"


class Shop(models.Model):
    """
    Модель магазина
    Поля:
        - name (str): Название магазина
        - url (str): Ссылка на файл продуктов магазина
        - description (str): Описание магазина
        - user (User): Пользователь
        - is_active (bool): Магазин активен
    """
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
    """
    Модель категории
    Поля:
        - name (str): Название категории
        - shops (Shop): Магазины
    """
    objects = models.manager.Manager()

    name = models.CharField(max_length=80, unique=True, verbose_name='Название категории')
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
    """
    Модель продукта
    Поля:
        - name (str): Название продукта
        - category (Category): Категория
    """
    objects = models.manager.Manager()

    name = models.CharField(max_length=100, unique=True, verbose_name='Название продукта')
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
    """
    Модель экземпляра продукта
    Поля:
        - product (Product): Продукт
        - shop (Shop): Магазин
        - quantity (int): Количество
        - preview (Image): Превью
        - price (int): Цена продукта
        - price_retail (int): Розничная цена продукта
    """
    objects = models.manager.Manager()

    article_id = models.IntegerField(blank=True, null=True, verbose_name='Артикул товара')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_items', verbose_name='Продукт')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='product_items', verbose_name='Магазин')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(10000)],
                                           verbose_name='Количество')
    preview = models.ImageField(upload_to="images/%Y/%m/%d", blank=True, null=True,
                                verbose_name='Превью')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена продукта',
                                validators=[MinValueValidator(Decimal('0.00'))])
    price_retail = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                       validators=[MinValueValidator(Decimal('0.00'))], verbose_name='Розничная цена продукта')

    class Meta:
        verbose_name = 'Описание продукта'
        verbose_name_plural = 'Список описаний продуктов'
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name}"


class Property(models.Model):
    """
    Модель свойства
    Поля:
        - name (str): Название
    """
    objects = models.manager.Manager()
    name = models.CharField(max_length=100, verbose_name='Название свойства')

    class Meta:
        verbose_name = 'Свойство'
        verbose_name_plural = 'Список свойств'
        ordering = ['-name']

    def __str__(self):
        return self.name


class ProductProperty(models.Model):
    """
    Модель свойства товара
    Поля:
        - product_item (ProductItem): Экземпляр продукта
        - property (Property): Свойство
        - value (str): Значение
    """
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
    """
    Модель контактов пользователя
    Поля:
        - user (User): Пользователь
        - phone (str): Номер телефона
        - country (str): Страна (опционально)
        - city (str): Город
        - street (str): Улица
        - house (str): Дом
        - structure (str): Корпус (опционально)
        - building (str): Строение (опционально)
        - apartment (str): Квартира
    """
    objects = models.manager.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts', blank=True, null=False,
                             verbose_name='Пользователь')
    phone  = models.CharField(max_length=20, blank=True, null=False, verbose_name='Номер телефона')
    country = models.CharField(max_length=30, blank=True, null=True, verbose_name='Страна')
    city = models.CharField(max_length=50, blank=True, null=False, verbose_name='Город')
    street = models.CharField(max_length=60, blank=True, null=False, verbose_name='Улица')
    house = models.CharField(max_length=20, blank=True, null=False, verbose_name='Номер дома')
    structure = models.CharField(max_length=20, blank=True, null=True, verbose_name='Корпус')
    building = models.CharField(max_length=20, blank=True, null=True, verbose_name='Строение')
    apartment = models.CharField(max_length=20, blank=True, null=False, verbose_name='Квартира')

    def __str__(self):
        return f"{self.user.email} - {self.phone}"

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов пользователей'

def default_valid_to():
    """
    Функция для генерации даты окончания действия купона по умолчанию
    """
    return timezone.now() + timedelta(days=30)

class Coupon(models.Model):
    """
    Модель купона
    Поля:
        - code (str): Код купона
        - valid_from (datetime): Дата начала действия купона
        - valid_to (datetime): Дата окончания действия купона
        - discount (int): Скидка
        - active (bool): Активен
        - created_at (datetime): Дата создания купона
    """
    objects = models.manager.Manager()

    code = models.CharField(max_length=60, unique=True, verbose_name='Код купона')
    valid_from = models.DateTimeField(default=timezone.now, verbose_name='Дата начала действия купона')
    valid_to = models.DateTimeField(default=default_valid_to,
                                    verbose_name='Дата окончания действия купона')
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                   verbose_name='Скидка', help_text='В процентах от 0 до 100')
    active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания купона')

    class Meta:
        verbose_name = 'Скидочный купон'
        verbose_name_plural = 'Список скидочных купонов'

    def __str__(self):
        return self.code

    def is_valid(self):
        return (self.valid_from <= timezone.now() <= self.valid_to) and self.active


class Order(models.Model):
    """
    Модель заказа
    Поля:
        - user (User): Пользователь
        - created_at (datetime): Дата создания заказа
        - state (str): Состояние заказа
        - contact (Contact): Контакт
        - coupon (Coupon): Купон (опционально)
    """
    objects = models.manager.Manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания заказа')
    state = models.CharField(choices=OrderStateChoices.choices, default=OrderStateChoices.PREPARING,
                                verbose_name='Состояние заказа')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True, related_name='orders',
                                verbose_name='Контакт')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Купон')

    def __str__(self):
        return f"{self.created_at} - {self.state}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ['-created_at']

    @property
    def total_price(self):
        if self.coupon and self.coupon.is_valid():
            discount = Decimal(1 - (self.coupon.discount / 100))
            return (Decimal(discount * sum(item.get_cost() for item in self.ordered_items.all()))
                    .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        return (Decimal(sum(item.get_cost() for item in self.ordered_items.all()))
                .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def is_valid(self):
        if not self.ordered_items.all():
            return False
        for item in self.ordered_items.all():
            is_active_shop = item.product_item.shop.is_active
            if item.product_item.quantity < item.quantity or is_active_shop is False:
                return False
        return True


class OrderItem(models.Model):
    """
    Модель позиции заказа
    Поля:
        - order (Order): Заказ
        - product_item (ProductItem): Экземпляр продукта
        - quantity (int): Количество
    """
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
        return Decimal(self.quantity * self.product_item.price)

    def __str__(self):
        return f"{self.product_item.product.name}"


class EmailTokenConfirm(models.Model):
    """
    Модель токена для подтверждения email
    Поля:
        - user (User): Пользователь
        - created_at (datetime): Дата создания токена
        - key (str): токен
    """
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
