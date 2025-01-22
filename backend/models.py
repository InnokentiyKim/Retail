from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class User(AbstractUser):
    class UserTypeChoices(models.TextChoices):
        seller = "Seller"
        buyer = "Buyer"

    type = models.TextField(choices=UserTypeChoices.choices, default=UserTypeChoices.buyer)

    def __str__(self):
        return f"{self.username} - {self.type} ({self.first_name} {self.last_name})"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Shop(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=100)
    url = models.URLField(max_length=300, blank=True, null=True)
    user = models.OneToOneField(User, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ['-name']


class Category(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = ''
        verbose_name_plural = ''
        ordering = ['-name']


class Product(models.Model):
    objects = models.manager.Manager()

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True, null=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ['-name']


class ProductDetails(models.Model):
    objects = models.manager.Manager()

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='details')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10000)])
    price = models.DecimalField(max_digits=10, decimal_places=2, positive=True)
    price_retail = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, positive=True)
    parameters = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        verbose_name = 'Описание продукта'
        verbose_name_plural = 'Описание продуктов'


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts', blank=True, null=True)
    phone  = models.CharField(max_length=20)
    country = models.CharField(max_length=30, blank=True, null=True)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=60)
    house = models.CharField(max_length=20, blank=True)
    structure = models.CharField(max_length=20, blank=True)
    building = models.CharField(max_length=20, blank=True)
    apartment = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}. Phone number is {self.phone}"

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = 'Список контактов'


class Order(models.Model):
    class OrderStateChoices(models.TextChoices):
        new = 'Новый'
        confirmed = 'Подтвержден'
        assembled = 'Собран'
        sent = 'Отправлен'
        delivered = 'Доставлен'
        canceled = 'Отменен'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=12, choices=OrderStateChoices.choices, default=OrderStateChoices.new)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, related_name='orders')

    def __str__(self):
        return f"{self.created_at} - {self.state}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Список позиций заказа'
