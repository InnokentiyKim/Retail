from django.urls import path
from backend.views import AccountRegisterView, AccountConfirmView, AccountView, SellerGoodsView, \
    CategoriesView, ShopsView, ProductItemView, ShoppingCartView, SellerStatusView, SellerOrdersView, \
    ContactView, BuyerOrdersView, CouponView, SellerShopView, PopularProductsView, ManagerOrdersView, \
    TokenObtain, TokenRefresh, AccountResetPasswordView, AccountResetPasswordConfirmView

app_name = 'backend'


urlpatterns = [
    path('user/register', AccountRegisterView.as_view(), name='user-register'),
    path('user/register/confirm', AccountConfirmView.as_view(), name='user-register-confirm'),
    path('user/account', AccountView.as_view(), name='user-account'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', TokenObtain.as_view(), name='token-obtain'),
    path('user/login/refresh', TokenRefresh.as_view(), name='token-refresh'),
    path('user/password_reset', AccountResetPasswordView.as_view(), name='password-reset'),
    path('user/password_reset/confirm', AccountResetPasswordConfirmView.as_view(), name='password-reset-confirm'),
    path('seller/goods', SellerGoodsView.as_view(), name='seller-goods'),
    path('seller/status', SellerStatusView.as_view(), name='seller-status'),
    path('seller/orders', SellerOrdersView.as_view(), name='seller-orders'),
    path('seller/shop', SellerShopView.as_view(), name='seller-shop'),
    path('shops', ShopsView.as_view(), name='shops'),
    path('products', ProductItemView.as_view(), name='products'),
    path('products/categories', CategoriesView.as_view(), name='product-categories'),
    path('products/popular', PopularProductsView.as_view(), name='popular-products'),
    path('buyer/shoppingcart', ShoppingCartView.as_view(), name='shoppingcart'),
    path('buyer/orders', BuyerOrdersView.as_view(), name='orders'),
    path('manager/orders', ManagerOrdersView.as_view(), name='manager-orders'),
    path('manager/coupons', CouponView.as_view(), name='manager-coupons'),
]