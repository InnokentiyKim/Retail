from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from backend.views import AccountRegisterView, AccountConfirmView, AccountView, SellerGoodsView, \
    CategoryView, ShopView, ProductItemView, ShoppingCartView, SellerStatusView, SellerOrdersView, \
    ContactView, OrderView, CouponView

app_name = 'backend'
urlpatterns = [
    path('user/register', AccountRegisterView.as_view(), name='user-register'),
    path('user/register/confirm', AccountConfirmView.as_view(), name='user-register-confirm'),
    path('user/account', AccountView.as_view(), name='user-account'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('user/login/refresh', TokenRefreshView.as_view(), name='token-refresh'),
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
    path('seller/goods', SellerGoodsView.as_view(), name='seller-goods'),
    path('seller/status', SellerStatusView.as_view(), name='seller-status'),
    path('seller/orders', SellerOrdersView.as_view(), name='seller-orders'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductItemView.as_view(), name='products'),
    path('shoppingcart', ShoppingCartView.as_view(), name='shoppingcart'),
    path('orders', OrderView.as_view(), name='orders'),
    path('coupons', CouponView.as_view(), name='coupons'),
]