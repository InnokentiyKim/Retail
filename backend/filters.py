from django_filters import rest_framework as filters
from backend.models import ProductItem


class ProductItemFilter(filters.FilterSet):
    shop_id = filters.NumberFilter(field_name='shop_id', lookup_expr='exact')
    category_id = filters.NumberFilter(field_name='product__category_id')
    search = filters.CharFilter(field_name='product__name', lookup_expr='icontains')
    ordering = filters.OrderingFilter(
        fields=(
            ('id', 'id'),
            ('product', 'product__name'),
            ('shop', 'shop__name'),
            ('price', 'price'),
        )
    )

    class Meta:
        model = ProductItem
        fields = ['shop_id', 'category_id', 'search', 'ordering']