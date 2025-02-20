from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.request import Request
from rest_framework.response import Response
from .models import EmailTokenConfirm, Shop, ProductItem, Order, \
    OrderStateChoices, OrderItem, Contact, Coupon
from .order import create_order_report
from .serializers import UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, ContactSerializer, \
    ProductItemSerializer, CouponSerializer, OrderItemUpdateSerializer, OrderItemCreateUpdateSerializer, \
    OrderItemDeleteSerializer, ContactDeleteSerializer, OrderStateSerializer
from rest_framework import status as http_status
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .signals import new_order
from .tasks import import_goods


class UserBackend:
    @staticmethod
    def register_account(request: Request):
        """
        Метод регистрирует нового пользователя в системе.
        Она принимает объект запроса, содержащий данные для регистрации,
        и возвращает объект ответа с результатом регистрации.

        Параметры:
            request (Request): Объект запроса, содержащий данные для регистрации:
            email, username, first_name, last_name, password, type.
        Возвращает:
            Response: Объект ответа со HTTP статусом:
                - 201 Created, если регистрация прошла успешно;
                - 409 Conflict, если регистрация не удалась;
                - 400 Bad Request, если данные запроса невалидны.
        Исключения:
            ValueError: Если данные запроса невалидны.
        """
        if {'email', 'username', 'first_name', 'last_name', 'password'}.issubset(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    with transaction.atomic():
                        user = user_serializer.save()
                        user.set_password(request.data['password'])
                        user.save()
                        return JsonResponse({'success': True}, status=http_status.HTTP_201_CREATED)
                else:
                    return JsonResponse({'success': False, 'errors': user_serializer.errors},
                                        status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': False, 'error': 'Some required fields are missing'},
                            status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def confirm_account(request):
        """
        Метод подтверждает регистрацию пользователя, используя email и токен,
        полученные в объекте запроса. Если данные пользователя валидны, то
        пользователь активируется

        Параметры:
            request (Request): Объект запроса, содержащий email и токен.
        Возвращает:
            Response: Объект ответа со статусом:
                - 200 OK, если подтверждение прошло успешно;
                - 400 Bad Request, если данные запроса невалидны;
        """
        if {'email', 'token'}.issubset(request.data):
            token = EmailTokenConfirm.objects.filter(
                user__email=request.data['email'],
                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            else:
                return JsonResponse({'success': False, 'error': 'Неверно указан email или токен'},
                                    status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': False}, status=http_status.HTTP_400_BAD_REQUEST)


    @staticmethod
    def get_account_info(request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @staticmethod
    def change_account_info(request):
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'success': False, 'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
            request.user.set_password(request.data['password'])

        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
        return JsonResponse({'success': False, 'errors': user_serializer.errors},
                                status=http_status.HTTP_400_BAD_REQUEST)


class SellerBackend:
    @staticmethod
    def import_seller_goods(request, *args, **kwargs):
        url = request.data.get('url')
        user_id = request.user.id
        if url is None:
            return JsonResponse({'error': 'url is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as error:
            return JsonResponse({'success': False, 'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
        import_goods.delay(url, user_id)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)


    @staticmethod
    def create_shop(request):
        serializer = ShopSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(user_id=request.user.id)
                return JsonResponse({'success': True}, status=http_status.HTTP_201_CREATED)
            except IntegrityError as err:
                return JsonResponse({'error': 'Your shop already exist'}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_status(request):
        shop = Shop.objects.filter(user_id=request.user.id).first()
        if shop is None:
            JsonResponse({'success': False, 'error': 'No shops found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    @staticmethod
    def change_status(request):
        seller_status = request.data.get('is_active')
        if seller_status is not None:
            try:
                Shop.objects.filter(user_id=request.user.id).update(is_active=bool(seller_status))
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            except IntegrityError as db_err:
                return JsonResponse({'success': False,'error': str(db_err)}, status=http_status.HTTP_400_BAD_REQUEST)
            except ValueError as val_err:
                return JsonResponse({'success': False, 'error': str(val_err)}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': False, 'error': 'state is_active is not specified or invalid'},
                            status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_orders(request):
        orders = Order.objects.filter(
            ordered_items__product_item__shop__user_id=request.user.id).exclude(
            state=OrderStateChoices.PREPARING).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties__property').select_related(
            'contact').distinct()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class BuyerBackend:
    @staticmethod
    def get_shopping_cart(request):
        cart = cache.get('cart')
        if not cart:
            cart = Order.objects.filter(
                user_id=request.user.id, state=OrderStateChoices.PREPARING).prefetch_related(
                'ordered_items__product__category').distinct()
            cache.set('cart', cart, 20)
        serializer = OrderSerializer(cart, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_update_shopping_cart(request):
        items_serializer = OrderItemCreateUpdateSerializer(request.data.get('items'), many=True)
        adding_items_dict = {}
        if items_serializer.is_valid():
            adding_items_dict = items_serializer.validated_data
        else:
            JsonResponse({'success': False, 'error': items_serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.PREPARING)
        for item in adding_items_dict:
            item.update({'order_id': cart.id})
            serializer = OrderItemSerializer(item)
            if serializer.is_valid():
                try:
                    serializer.save()
                except IntegrityError as err:
                    return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
            else:
                return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)

    @staticmethod
    def update_shopping_cart(request):
        serializer = OrderItemUpdateSerializer(request.data.get('items'), many=True)
        if serializer.is_valid():
            updating_items_dict = serializer.validated_data
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.PREPARING)
        for item in updating_items_dict:
            try:
                OrderItem.objects.filter(order_id=cart.id, id=item['id']).update(quantity=item['quantity'])
            except IntegrityError as err:
                return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)

    @staticmethod
    def delete_shopping_cart_items(request):
        serializer = OrderItemDeleteSerializer(request.data.get('items'), many=True)
        if serializer.is_valid():
            deleting_items_dict = serializer.validated_data
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        cart = Order.objects.filter(user_id=request.user.id, state=OrderStateChoices.PREPARING).first()
        if cart is None:
            return JsonResponse({'success': False, 'error': 'No order found'}, status=http_status.HTTP_404_NOT_FOUND)
        query = Q()
        for item in deleting_items_dict:
            query |= Q(order_id=cart.id, id=item['id'])
        try:
            OrderItem.objects.filter(query).delete()
        except IntegrityError as err:
            return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': True}, status=http_status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get_order(request):
        order = (Order.objects.filter(user_id=request.user.id,
            state=OrderStateChoices.PREPARING).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties'
        ).select_related('contact').distinct())
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    @staticmethod
    def confirm_order(request, sender):
        coupon = None
        if not {'id', 'contact'}.issubset(request.data) or not request.data['id'].isdigit():
            return JsonResponse({'success': False}, status=http_status.HTTP_400_BAD_REQUEST)
        contact_data = request.data['contact']
        contact_serializer = ContactSerializer(data=contact_data)
        if not contact_serializer.is_valid():
            return JsonResponse({'success': False, 'error': contact_serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        coupon_code = request.data.get('coupon_code')
        if coupon_code:
            coupon = Coupon.objects.filter(code__exact=coupon_code).first()
            if coupon is None or not coupon.is_valid():
                return JsonResponse({'success': False, 'error': 'Coupon not found or invalid'},
                                    status=http_status.HTTP_400_BAD_REQUEST)
        order = Order.objects.get(user_id=request.user.id, id=request.data['id']).first()
        if order is None:
            return JsonResponse({'success': False, 'error': 'Order not found'}, status=http_status.HTTP_404_NOT_FOUND)
        if coupon:
            order.coupon_id = coupon.id
        order.contact_id = contact_data['id']
        order.state = OrderStateChoices.CREATED
        try:
            order.save()
        except IntegrityError as err:
            return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        report_filename = create_order_report(order)
        new_order.send(sender=sender, user_id=request.user.id, order_state=order.state, report=report_filename)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)


class ContactBackend:
    @staticmethod
    def get_contacts(request):
        contacts = cache.get('contacts')
        if not contacts:
            contacts = Contact.objects.filter(user_id=request.user.id)
            cache.set('contacts', contacts, 20)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_contact(request):
        serializer = ContactSerializer(data={**request.data, 'user': request.user.id})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True}, status=http_status.HTTP_201_CREATED)
        return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update_contact(request):
        if 'id' in request.data and request.data['id'].isdigit():
            contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
            if contact is None:
                return JsonResponse({'success': False}, status=http_status.HTTP_404_NOT_FOUND)
            serializer = ContactSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            else:
                return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete_contact(request):
        serializer = ContactDeleteSerializer(request.data.get('items'))
        if serializer.is_valid():
            deleting_items_dict = serializer.validated_data
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        if deleting_items_dict:
            query = Q()
            for item in deleting_items_dict:
                query |= Q(user_id=request.user.id, id=item['id'])
            try:
                Contact.objects.filter(query).delete()
                return JsonResponse({'success': True}, status=http_status.HTTP_204_NO_CONTENT)
            except IntegrityError as err:
                return JsonResponse({'success': False}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': False, 'error': 'No deleting items found'}, status=http_status.HTTP_400_BAD_REQUEST)


class ProductsBackend:
    @staticmethod
    def get_products(self, request):
        products = cache.get('products')
        if not products:
            products = ProductItem.objects.filter(shop__is_active=True).select_related(
                'shop', 'product__category', 'product_name').distinct()
            products = self.filter_queryset(products)
            cache.set('products', products, 20)
        serializer = ProductItemSerializer(products, many=True)
        return Response(serializer.data)


class CouponBackend:
    @staticmethod
    def get_coupons(request):
        coupons = cache.get('coupons')
        if not coupons:
            coupons = Coupon.objects.all()
            cache.set('coupons', coupons, 30)
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_coupon(request):
        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return JsonResponse({'success': True}, status=http_status.HTTP_201_CREATED)
            except IntegrityError as err:
                return JsonResponse({'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update_coupon(request):
        if 'id' in request.data and request.data['id'].isdigit():
            coupon = Coupon.objects.filter(id=request.data['id']).first()
            if coupon is None:
                return JsonResponse({'success': False}, status=http_status.HTTP_404_NOT_FOUND)
            serializer = CouponSerializer(coupon, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            else:
                return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': False}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete_coupon(request):
        if 'id' in request.data and request.data['id'].isdigit():
            try:
                Coupon.objects.filter(id=request.data['id']).delete()
                return JsonResponse({'success': True}, status=http_status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist as err:
                return JsonResponse({'error': str(err)}, status=http_status.HTTP_404_NOT_FOUND)
            except IntegrityError as err:
                return JsonResponse({'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': False}, status=http_status.HTTP_400_BAD_REQUEST)


class ManagerBackend:
    @staticmethod
    def get_orders(request):
        orders = cache.get('orders')
        if not orders:
            orders = (Order.objects.all().exclude(
                state=OrderStateChoices.PREPARING).prefetch_related(
                'ordered_items__product_item__product__category',
                'ordered_items__product_item__product_properties'
            ).select_related('contact').distinct())
            cache.set('orders', orders, 20)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @staticmethod
    def change_orders_state(request):
        serializer = OrderStateSerializer(data=request.data)
        if serializer.is_valid():
            order = Order.objects.filter(id=request.data['id']).first()
            if order is None:
                return JsonResponse({'success': False}, status=http_status.HTTP_404_NOT_FOUND)
            order.state = request.data['state']
            try:
                order.save()
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            except IntegrityError as err:
                return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': False}, status=http_status.HTTP_400_BAD_REQUEST)
