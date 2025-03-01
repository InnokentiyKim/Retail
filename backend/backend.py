import redis
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.request import Request
from rest_framework.response import Response
from .models import EmailTokenConfirm, Shop, ProductItem, Order, \
    OrderStateChoices, OrderItem, Contact, Coupon, Product
from .order import create_order_report, update_ordered_items_quantity, get_mail_attachment
from .serializers import UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, ContactSerializer, \
    ProductItemSerializer, CouponSerializer, OrderItemUpdateSerializer, OrderItemCreateUpdateSerializer, \
    OrderItemDeleteSerializer, OrderStateSerializer, OrderConfirmSerializer, ProductSerializer, \
    ContactUpdateSerializer, ContactDeleteSerializer, CouponDeleteSerializer, CouponCreateSerializer
from rest_framework import status as http_status
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .signals import new_order
from .tasks import import_goods


redis_db = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


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
        """
        Метод возвращает информацию о пользователе, сделавшим запрос

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: Объект ответа, содержащий информацию о пользователе:
                id, email, username, first_name, last_name, type, contacts.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @staticmethod
    def change_account_info(request):
        """
        Метод обновляет информацию об аккаунте пользователя

        Параметры:
            request (Request): Объект запроса, содержащий данные пользователя для обновления.
                Если включен 'password', он будет проверен и установлен для пользователя.
        Возвращает:
            JsonResponse: Ответ в JSON формате, содержащий:
                - {'success': True} с HTTP статусом 200 при успешном обновлении информации.
                - {'success': False, 'error': <error_message>} с HTTP статусом 400 при ошибке валидации пароля
                - {'success': False, 'errors': <serializer_errors>} с HTTP статусом 400 при ошибке валидации переданных данных
        """
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return JsonResponse({'success': False, 'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
            request.user.set_password(request.data['password'])

        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            try:
                user_serializer.save()
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            except IntegrityError as err:
                return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': False, 'errors': user_serializer.errors},
                                status=http_status.HTTP_400_BAD_REQUEST)


class SellerBackend:
    @staticmethod
    def import_seller_goods(request, *args, **kwargs):
        """
        Метод инициирует импорт товаров продавца из YAML-файла по указанному URL.
        Он проверяет наличие и формат URL. Если URL действителен, он запускает асинхронную задачу для импорта товаров.

        Параметры:
            request (Request): Объект запроса, содержащий URL YAML-файла для импорта.
        Возвращает:
            JsonResponse: Ответ в JSON формате, содержащий:
                - {'success': True, 'message': 'Import started'} с HTTP статусом 200 если импорт успешно запущен.
                - {'error': 'url is required'} с HTTP статусом 400 если URL отсутствует в запросе.
                - {'success': False, 'error': <error_message>} с HTTP статусом 400 если URL невалиден.
        """
        url = request.data.get('url')
        user_id = request.user.id
        if url is None:
            return JsonResponse({'error': 'url is required'}, status=http_status.HTTP_400_BAD_REQUEST)
        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as error:
            return JsonResponse({'success': False, 'error': str(error)}, status=http_status.HTTP_400_BAD_REQUEST)
        shop = Shop.objects.filter(user_id=user_id).first()
        if shop is None:
            return JsonResponse({'success': False, 'error': 'Shop not found'}, status=http_status.HTTP_404_NOT_FOUND)
        import_goods.delay(url, shop.id, user_id)
        return JsonResponse({'success': True, 'message': 'Import started'}, status=http_status.HTTP_200_OK)


    @staticmethod
    def create_shop(request):
        """
        Метод создает новый магазин для зарегистрированного пользователя
        Он проверяет наличие и формат данных магазина. Если данные валидны, он сохраняет магазин
        с привязкой к current user.

        Параметры:
            request (Request): Объект запроса, содержащий данные магазина.
        Возвращает:
            JsonResponse: Ответ в JSON формате, содержащий:
                - {'success': True} с HTTP статусом 201, если магазин создан.
                - {'error': 'Your shop already exist'} с HTTP статусом 409, если магазин с такими данными уже существует.
                - {'error': <serializer_errors>} с HTTP статусом 400, если переданные данные магазина не валидны.
        """
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
        """
        Метод возвращает информацию о магазине, принадлежащем текущему пользователю

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: Объект ответа, содержащий информацию о магазине:
                id, name, is_active.
        """
        shop = Shop.objects.filter(user_id=request.user.id).first()
        if shop is None:
            JsonResponse({'success': False, 'error': 'No shops found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    @staticmethod
    def change_status(request):
        """
        Метод изменяет статус продавца.
        Он получает из запроса флаг is_active и изменяет статус магазина с id текущего пользователя.

        Параметры:
            request (Request): Объект запроса, содержащий флаг is_active (bool).
        Возвращает:
            JsonResponse: Ответ в JSON формате, содержащий:
                - {'success': True} с HTTP статусом 200, если статус успешно изменен.
                - {'success': False, 'error': <error_message>} с HTTP статусом 400, если флаг is_active не указан.
                - {'success': False, 'errors': <serializer_errors>} с HTTP статусом 409, если статус не может быть изменен.
        """
        seller_status = request.data.get('is_active')
        if seller_status is not None:
            try:
                Shop.objects.filter(user_id=request.user.id).update(is_active=bool(seller_status))
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            except IntegrityError as db_err:
                return JsonResponse({'success': False,'error': str(db_err)}, status=http_status.HTTP_409_CONFLICT)
            except ValueError as val_err:
                return JsonResponse({'success': False, 'error': str(val_err)}, status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': False, 'error': 'state is_active is not specified or invalid'},
                            status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_orders(request):
        """
        Метод возвращает список заказов, связанных с магазином текущего пользователя

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: Объект ответа, содержащий список заказов с информацией о них:
                id, ordered_items, created_at, state, contact, total_price
        """
        cache_key = f'seller_orders_{request.user.id}'
        orders = cache.get(cache_key)
        if not orders:
            orders = Order.objects.filter(
                ordered_items__product_item__shop__user_id=request.user.id).exclude(
                state=OrderStateChoices.PREPARING).prefetch_related(
                'ordered_items__product_item__product__category',
                'ordered_items__product_item__product_properties__property').select_related(
                'contact').distinct()
            if orders is None:
                return JsonResponse({'success': False, 'error': 'No orders found'}, status=http_status.HTTP_404_NOT_FOUND)
            cache.set(cache_key, orders, 60)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @staticmethod
    def get_seller_products(request):
        """
        Метод возвращает список товаров, относящихся к магазину текущего пользователя

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: Объект ответа, содержащий список товаров продавца
        """
        products = ProductItem.objects.filter(shop__user_id=request.user.id).select_related(
            'product').distinct()
        if products is None:
            return JsonResponse({'success': False, 'error': 'No products found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = ProductItemSerializer(products, many=True)
        return Response(serializer.data)


class ProductsBackend:
    @staticmethod
    def get_products(self, request):
        """
        Метод возвращает список товаров, относящихся к активным магазинам.
        Он использует кэширование, чтобы уменьшить нагрузку на БД.

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: Объект ответа, содержащий список товаров с информацией о них:
                id, product, shop, quantity, preview, price, price_retail, product_properties
        """
        cache_key = 'all_products'
        products = cache.get(cache_key)
        if not products:
            products = ProductItem.objects.filter(shop__is_active=True, quantity__gt=0).select_related(
                'shop', 'product').distinct()
            if products is None:
                return JsonResponse({'success': False, 'error': 'No products found'}, status=http_status.HTTP_404_NOT_FOUND)
            cache.set(cache_key, products, 60 * 5)
        serializer = ProductItemSerializer(products, many=True)
        return Response(serializer.data)

    @staticmethod
    def update_product_ranking(product_ids: list[int]) -> None:
        """
        Обновляет рейтинг товаров в Redis.
        Этот метод принимает список идентификаторов товаров и увеличивает их рейтинг в Redis на единицу.
        Рейтинг товаров хранится в Redis в виде отсортированного множества с именем 'product_ranking'.

        Параметры:
            product_ids (list[int]): Список идентификаторов товаров, рейтинг которых нужно обновить.
        Возвращает:
            None
        """
        for product_id in product_ids:
            redis_db.zincrby(name='product_ranking', amount=1, value=product_id)
        return None

    @staticmethod
    def get_product_ranking(count: int):
        """
        Возвращает список самых популярных товаров.
        Этот метод извлекает из Redis рейтинг товаров и возвращает список самых популярных товаров.
        Рейтинг товаров хранится в Redis в виде отсортированного множества с именем 'product_ranking'.

        Параметры:
            count (int): Количество самых популярных товаров, которые нужно вернуть.
        Возвращает:
            list[Product]: Список самых популярных товаров, отсортированных по их рейтингу.
        """
        product_ranking = redis_db.zrange('product_ranking', 0, -1, desc=True)[:count]
        product_ranking_ids = [int(prod_id) for prod_id in product_ranking]
        most_popular_products = list(Product.objects.filter(id__in=product_ranking_ids))
        most_popular_products.sort(key=lambda x: product_ranking_ids.index(x.id))
        serializer = ProductSerializer(most_popular_products, many=True)
        if serializer.data is None:
            return JsonResponse({'success': False, 'error': 'No products found'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=http_status.HTTP_200_OK)


class BuyerBackend:
    @staticmethod
    def get_shopping_cart(request):
        """
        Возвращает корзину покупателя.
        Корзина покупателя содержит список заказанных товаров, их свойства и категории.

        Параметры:
            request (Request): Объект запроса, содержащий информацию о пользователе.
        Возвращает:
            Response: JSON-ответ, содержащий данные о корзине покупателя.
                - Если корзина найдена, возвращает список заказанных товаров в формате JSON.
                - Если корзина не найдена, возвращает ошибку со статусом HTTP 404.
        """
        cart = (Order.objects.filter(user_id=request.user.id,
                                      state=OrderStateChoices.PREPARING).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties__property'
        ).select_related('contact').distinct())
        if cart is None:
            return JsonResponse({'success': False, 'error': 'No cart found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(cart, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_update_shopping_cart(request):
        """
        Создает и/или обновляет корзину покупателя.
        Этот метод принимает список товаров, которые нужно добавить в корзину, и обновляет корзину покупателя.
        Если корзина не существует, она создается автоматически.

        Параметры:
            request (Request): Объект запроса, содержащий список товаров для добавления в корзину.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если корзина создана или обновлена успешно, возвращает {'success': True} со статусом HTTP 200.
                - Если данные о товарах невалидны, возвращает ошибку со статусом HTTP 400.
                - Если возникает конфликт при сохранении товара, возвращает ошибку со статусом HTTP 409.
        """
        items_serializer = OrderItemCreateUpdateSerializer(data=request.data, many=True)
        adding_items_list = []
        if items_serializer.is_valid():
            adding_items_list = items_serializer.validated_data
        else:
            JsonResponse({'success': False, 'error': str(items_serializer.errors)}, status=http_status.HTTP_400_BAD_REQUEST)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.PREPARING)
        for item in adding_items_list:
            item.update({'order': cart.id})
            serializer = OrderItemSerializer(data=item)
            if serializer.is_valid():
                try:
                    serializer.save()
                except IntegrityError as err:
                    return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
            else:
                JsonResponse({'success': False, 'error': str(items_serializer.errors)},
                             status=http_status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)

    @staticmethod
    def update_shopping_cart(request):
        """
        Обновляет количество товаров в корзине.
        Этот метод принимает список товаров и обновляет количество товаров в корзине.
        Если корзина не существует, она создается автоматически.

        Параметры:
            request (Request): Объект запроса, содержащий список товаров их количества для обновления в корзине.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если корзина обновлена успешно, возвращает {'success': True} со статусом HTTP 200.
                - Если данные о товарах невалидны, возвращает ошибку со статусом HTTP 400.
                - Если не удалось обновить товар в БД, возвращает ошибку со статусом HTTP 409.
        """
        serializer = OrderItemUpdateSerializer(data=request.data, many=True)
        if serializer.is_valid():
            updating_items_list = serializer.validated_data
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        cart, _ = Order.objects.get_or_create(user_id=request.user.id, state=OrderStateChoices.PREPARING)
        for item in updating_items_list:
            try:
                OrderItem.objects.filter(order_id=cart.id, id=item['id']).update(quantity=item['quantity'])
            except IntegrityError as err:
                return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)

    @staticmethod
    def delete_shopping_cart_items(request):
        """
            Удаляет товары из корзины покупателя.
            Этот метод принимает список товаров, которые нужно удалить из корзины.
            Если корзина не существует, возвращает ошибку.

            Параметры:
                request (Request): Объект запроса, содержащий список товаров для удаления из корзины.
            Возвращает:
                JsonResponse: JSON-ответ, содержащий результат операции.
                    - Если товары удалены успешно, возвращает {'success': True} со статусом HTTP 204.
                    - Если данные о товарах невалидны, возвращает ошибку со статусом HTTP 400.
                    - Если корзина не найдена, возвращает ошибку со статусом HTTP 404.
                    - Если возникает конфликт при удалении товара из БД, возвращает ошибку со статусом HTTP 409.
            """
        serializer = OrderItemDeleteSerializer(data=request.data)
        if serializer.is_valid():
            deleting_items_list = serializer.validated_data['items']
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        cart = Order.objects.filter(user_id=request.user.id, state=OrderStateChoices.PREPARING).first()
        if cart is None:
            return JsonResponse({'success': False, 'error': 'No active shopping cart found'},
                                status=http_status.HTTP_404_NOT_FOUND)
        query = Q()
        for item_id in deleting_items_list:
            query |= Q(order_id=cart.id, id=item_id)
        try:
            deleted_items_count = OrderItem.objects.filter(query).delete()[0]
        except IntegrityError as err:
            return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        if deleted_items_count > 0:
            return JsonResponse({'success': True, 'message': f'Deleted {deleted_items_count} item(s)'},
                                status=http_status.HTTP_204_NO_CONTENT)
        return JsonResponse({'success': False, 'error': 'No items found to delete'}, status=http_status.HTTP_404_NOT_FOUND)

    @staticmethod
    def get_orders(request):
        """
        Возвращает историю заказов покупателя.
        Метод использует кэш для ускорения работы и снижения нагрузки на базу данных.

        Параметры:
            request (Request): Объект запроса, содержащий информацию о пользователе.
        Возвращает:
            Response: JSON-ответ, содержащий список заказов покупателя.
                - Ответ со статусом HTTP 200 при успешном получении списка заказов.
                - Если список заказов не найден, возвращает ошибку со статусом HTTP 404.
        """
        cache_key = f'buyer_orders_{request.user.id}'
        orders = cache.get(cache_key)
        if not orders:
            orders = (Order.objects.filter(user_id=request.user.id).exclude(
                state=OrderStateChoices.PREPARING).prefetch_related(
                'ordered_items__product_item__product__category',
                'ordered_items__product_item__product_properties__property'
            ).select_related('contact').distinct())
            if orders is None:
                return JsonResponse({'success': False, 'error': 'No orders found'}, status=http_status.HTTP_404_NOT_FOUND)
            cache.set(cache_key, orders, 60 * 3)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @staticmethod
    def confirm_order(request, sender):
        """
        Метод для подтверждения заказа покупателя.
        Если заказ успешно подтвержден, изменяет статус заказа, генерирует отчет о заказе и отправляет уведомление
        по email о новом заказе с прикрепленным отчетом.
        Также при успешном подтверждении заказа обновляет количество оставшихся товаров магазина и обновляет статистику
        самых популярных товаров.

        Параметры:
            request (Request): Объект запроса, содержащий данные о заказе:
                - id (int): Идентификатор заказа.
                - contact (int): Идентификатор контакта.
                - coupon (str, optional): Скидочный купон.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если заказ успешно подтвержден, возвращает {'success': True} со статусом HTTP 200.
                - Если данные о заказе невалидны или введен невалидный/неверный купон, возвращает ошибку со статусом HTTP 400.
                - Если заказ или контакт не найден, возвращает ошибку со статусом HTTP 404.
                - Если возникает конфликт при сохранении заказа в БД, возвращает ошибку со статусом HTTP 409.
        """
        serializer = OrderConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        order_id = serializer.validated_data.get('id')
        contact_id = serializer.validated_data.get('contact')
        order = Order.objects.filter(user_id=request.user.id, id=order_id, state=OrderStateChoices.PREPARING).first()
        contact = Contact.objects.filter(user_id=request.user.id, id=contact_id).first()
        if order is None or contact is None:
            return JsonResponse({'success': False, 'error': 'Active shopping cart or contact not found'},
                                status=http_status.HTTP_404_NOT_FOUND)
        if not order.is_valid():
            return JsonResponse(
                {'success': False, 'error': 'Shops product quantity is not enough to confirm your order or order is empty'},
                status=http_status.HTTP_400_BAD_REQUEST)
        coupon_code = serializer.validated_data.get('coupon_code')
        if coupon_code:
            coupon = Coupon.objects.filter(code__exact=coupon_code).first()
            if coupon is None or not coupon.is_valid():
                return JsonResponse({'success': False, 'error': 'Coupon not found or invalid'},
                                    status=http_status.HTTP_400_BAD_REQUEST)
            order.coupon_id = coupon.id
        order.contact_id = contact_id
        order.state = OrderStateChoices.CREATED
        try:
            order.save()
        except IntegrityError as err:
            return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        update_ordered_items_quantity(order)
        product_ids = [item.product_item.product_id for item in order.ordered_items.all()]
        ProductsBackend.update_product_ranking(product_ids)
        report_path = create_order_report(order)
        attachment = get_mail_attachment(report_path)
        new_order.send(sender=sender, user_id=request.user.id, order_id=order.id, order_state=order.state, report_file=attachment)
        return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)


class ContactBackend:
    @staticmethod
    def get_contacts(request):
        """
        Возвращает список контактов пользователя.

        Параметры:
            request (Request): Объект запроса, содержащий информацию о пользователе.
        Возвращает:
            Response: JSON-ответ, содержащий список контактов пользователя.
                - Если список контактов найден, возвращает его в ответе в формате JSON.
                - Если список контактов не найден, возвращает ошибку со статусом HTTP 404.
        """
        contacts = Contact.objects.filter(user_id=request.user.id)
        if contacts is None:
            return JsonResponse({'success': False, 'error': 'No contacts found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_contact(request):
        """
        Метод для создания нового контакта пользователя.

        Параметры:
            request (Request): Объект запроса, содержащий данные о контакте:
                - id (int): Идентификатор контакта.
                - phone (str): Телефон контакта.
                - city (str): Город контакта.
                - street (str): Улица контакта.
                - house (str): Дом контакта.
                - apartment (str): Квартира контакта.
                - country, structure, building (str): Дополнительные поля контакта (опционально).

        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если контакт успешно создан, возвращает {'success': True} со статусом HTTP 201.
                - Если данные о контакте невалидны, возвращает ошибку со статусом HTTP 400.
        """
        serializer = ContactSerializer(data={**request.data, 'user': request.user.id})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True}, status=http_status.HTTP_201_CREATED)
        return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update_contact(request):
        """
        Обновляет существующий контакт пользователя.

        Параметры:
            request (Request): Объект запроса, содержащий данные о контакте:
                - id (int): Идентификатор контакта.
                - <parameter_name> (str): Значение параметра контакта.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если контакт успешно обновлен, возвращает {'success': True} со статусом HTTP 200.
                - Если данные о контакте невалидны, возвращает ошибку со статусом HTTP 400.
                - Если контакт не найден, возвращает ошибку со статусом HTTP 404.
        """
        request_serializer = ContactUpdateSerializer(data=request.data)
        if not request_serializer.is_valid():
            return JsonResponse({'success': False, 'error': request_serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        contact = Contact.objects.filter(id=request_serializer.validated_data['id'], user_id=request.user.id).first()
        if contact is None:
            return JsonResponse({'success': False}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = ContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete_contact(request, *args, **kwargs):
        """
        Метод для удаления контактов пользователя.

        Параметры:
            - items(list[int]) - список ID контактов для удаления.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если контакты успешно удалены, возвращает {'success': True} со статусом HTTP 204.
                - Если данные о контактах невалидны или список контактов пуст, возвращает ошибку со статусом HTTP 400.
                - Если переданные контакты не найдены, то возвращает ошибку со статусом HTTP 404.
        """
        serializer = ContactDeleteSerializer(data=request.data)
        if serializer.is_valid():
            deleting_items_list = serializer.validated_data.get('items')
        else:
            return JsonResponse({'success': False, 'error': serializer.errors}, status=http_status.HTTP_400_BAD_REQUEST)
        if deleting_items_list:
            query = Q()
            for item_id in deleting_items_list:
                query |= Q(user_id=request.user.id, id=item_id)
            deleted_contacts_count = Contact.objects.filter(query).delete()[0]
            if deleted_contacts_count > 0:
                return JsonResponse({'success': True, "message": f"deleted {deleted_contacts_count} item(s)"},
                                    status=http_status.HTTP_204_NO_CONTENT)
        return JsonResponse({'success': False, 'error': 'No items found to delete'}, status=http_status.HTTP_404_NOT_FOUND)


class CouponBackend:
    @staticmethod
    def get_coupons(request):
        """
        Возвращает список всех существующих купонов.

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: JSON-ответ, содержащий список купонов.
        """
        coupons = Coupon.objects.all()
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)

    @staticmethod
    def create_coupon(request):
        """
        Метод для создания нового купона.

        Параметры:
            request (Request): Объект запроса, содержащий данные о купоне:
                - code (str): Код купона.
                - valid_from (date): Дата начала действия купона.
                - valid_to (date): Дата окончания действия купона.
                - discount (int): Процент скидки.
                - active (bool): Флаг активности купона.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если купон успешно создан, возвращает {'success': True} со статусом HTTP 201.
                - Если данные о купоне невалидны, возвращает ошибку со статусом HTTP 400.
                - Если возникает конфликт при создании купона, возвращает ошибку со статусом HTTP 409.
        """
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
        """
        Обновляет существующий купон.

        Параметры:
            request (Request): Объект запроса, содержащий данные о купоне:
                - id (str): Идентификатор купона.
                - <parameter_name> (str): Значение параметра купона.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если купон успешно обновлен, возвращает {'success': True} со статусом HTTP 200.
                - Если данные о купоне невалидны, возвращает ошибку со статусом HTTP 400.
                - Если купон не найден, возвращает ошибку со статусом HTTP 404.
        """
        request_serializer = CouponCreateSerializer(data=request.data, partial=True)
        if request_serializer.is_valid():
            validated_data = request_serializer.validated_data
        else:
            return JsonResponse({'success': False, 'error': str(request_serializer.errors)},
                                status=http_status.HTTP_400_BAD_REQUEST)
        coupon = Coupon.objects.filter(id=validated_data.get('id')).first()
        if coupon is None:
            return JsonResponse({'success': False, 'error': 'Coupon not found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = CouponSerializer(coupon, data=validated_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
        else:
            return JsonResponse({'success': False, 'error': str(serializer.errors)}, status=http_status.HTTP_409_CONFLICT)

    @staticmethod
    def delete_coupon(request, *args, **kwargs):
        """
        Удаляет существующий купон.

        Параметры:
            - <coupon_id> (int): Идентификатор купона. Параметр пути запроса.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если купон успешно удален, возвращает {'success': True} со статусом HTTP 204.
                - Если купон не найден, возвращает ошибку со статусом HTTP 404.
                - Если возникает конфликт при удалении купона, возвращает ошибку со статусом HTTP 409.
        """
        serializer = CouponDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse({'success': False, 'error': str(serializer.errors)}, status=http_status.HTTP_400_BAD_REQUEST)
        deleting_items_list = serializer.validated_data.get('items')
        if deleting_items_list:
            query = Q()
            for item_id in deleting_items_list:
                query |= Q(id=item_id)
            deleted_coupons_count = Coupon.objects.filter(query).delete()[0]
            if deleted_coupons_count > 0:
                return JsonResponse({'success': True, 'message': f'Deleted {deleted_coupons_count} item(s)'},
                                    status=http_status.HTTP_204_NO_CONTENT)
        return JsonResponse({'success': False, 'error': 'No items found to delete'},
                            status=http_status.HTTP_400_BAD_REQUEST)

class ManagerBackend(CouponBackend):
    @staticmethod
    def get_orders(request):
        """
        Возвращает список всех заказов.

        Параметры:
            request (Request): Объект запроса.
        Возвращает:
            Response: JSON-ответ, содержащий список заказов, включая список заказанных товаров, их свойства и категории.
                - Если список заказов найден, возвращает список заказов в формате JSON.
                - Если список заказов не найден, возвращает ошибку со статусом HTTP 404.
        """
        orders = (Order.objects.all().exclude(
            state=OrderStateChoices.PREPARING).prefetch_related(
            'ordered_items__product_item__product__category',
            'ordered_items__product_item__product_properties__property'
        ).select_related('contact').distinct())
        if orders is None:
            return JsonResponse({'success': False, 'error': 'No orders found'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @staticmethod
    def change_orders_state(request, sender, *args, **kwargs):
        """
        Метод для изменения состояния заказа.

        Параметры:
            request (Request): Объект запроса, содержащий данные о заказе:
                - id (str): Идентификатор заказа.
                - state (str): Новое состояние заказа.
        Возвращает:
            JsonResponse: JSON-ответ, содержащий результат операции.
                - Если состояние заказа успешно изменено, возвращает {'success': True} со статусом HTTP 200.
                - Если данные о заказе невалидны, возвращает ошибку со статусом HTTP 400.
                - Если заказ не найден, возвращает ошибку со статусом HTTP 404.
                - Если возникает конфликт при изменении состояния заказа, возвращает ошибку со статусом HTTP 409.
        """
        serializer = OrderStateSerializer(data=request.data)
        if serializer.is_valid():
            order = Order.objects.filter(id=request.data['id']).first()
            if order is None:
                return JsonResponse({'success': False}, status=http_status.HTTP_404_NOT_FOUND)
            order.state = request.data['state']
            try:
                order.save()
                new_order.send(sender=sender, user_id=order.user_id, order_id=order.id, order_state=order.state)
                if order.state == OrderStateChoices.CANCELED:
                    update_ordered_items_quantity(order)
                return JsonResponse({'success': True}, status=http_status.HTTP_200_OK)
            except IntegrityError as err:
                return JsonResponse({'success': False, 'error': str(err)}, status=http_status.HTTP_409_CONFLICT)
        return JsonResponse({'success': False, 'error': str(serializer.errors)}, status=http_status.HTTP_400_BAD_REQUEST)
