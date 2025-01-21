from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Shop(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=300)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    shops = models.ManyToManyField(Shop, blank=True, related_name='categories')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True, nullable=True)

    def __str__(self):
        return self.name


class ProductDetails(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='details')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(1000)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    parameters = models.JSONField(default=dict, blank=True, nullable=True)


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
        return self.phone


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
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True, related_name='orders')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)