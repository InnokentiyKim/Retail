from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm
from backend.views import AccountRegisterView, AccountConfirmView, AccountView, LoginAccountView, SellerGoodsView, \
    CategoryView, ShopView, ProductDetailsView, ShoppingCartView, SellerStatusView, SellerOrdersView, \
    ContactView, OrderView


urlpatterns = [
    path('SELLER/goods', SellerGoodsView.as_view(), name='SELLER-goods'),
    path('SELLER/status', SellerStatusView.as_view(), name='SELLER-status'),
    path('SELLER/orders', SellerOrdersView.as_view(), name='SELLER-orders'),
    path('user/register', AccountRegisterView.as_view(), name='user-register'),
    path('user/register/confirm', AccountConfirmView.as_view(), name='user-register-confirm'),
    path('user/info', AccountView.as_view(), name='user-info'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', LoginAccountView.as_view(), name='user-login'),
    path('user/password_reset', reset_password_request_token, name='password_reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password_reset_confirm'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductDetailsView.as_view(), name='products'),
    path('shoppingcart', ShoppingCartView.as_view(), name='shoppingcart'),
    path('orders', OrderView.as_view(), name='orders'),
]