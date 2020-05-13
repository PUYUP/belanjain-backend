from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .shipping.views import ShippingAddressApiView
from .purchase.views import PurchaseApiView
from .necessary.views import NecessaryApiView
from .goods.views import GoodsApiView
from .catalog.views import CatalogApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('shipping-address', ShippingAddressApiView, basename='shipping_address')
router.register('purchases', PurchaseApiView, basename='purchase')
router.register('necessaries', NecessaryApiView, basename='necessary')
router.register('goods', GoodsApiView, basename='goods')
router.register('catalogs', CatalogApiView, basename='catalog')

app_name = 'shoptask'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
