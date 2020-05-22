from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .customer.shipping.views import ShippingAddressApiView
from .customer.purchase.views import PurchaseApiView
from .customer.necessary.views import NecessaryApiView
from .customer.goods.views import GoodsApiView
from .customer.catalog.views import CatalogApiView
from .customer.base.views import CategoryApiView, BrandApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('shipping-address', ShippingAddressApiView,
                basename='shipping_address')
router.register('purchases', PurchaseApiView, basename='purchase')
router.register('necessaries', NecessaryApiView, basename='necessary')
router.register('goods', GoodsApiView, basename='goods')
router.register('catalogs', CatalogApiView, basename='catalog')
router.register('categories', CategoryApiView, basename='category')
router.register('brands', BrandApiView, basename='brand')

app_name = 'shoptask'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
