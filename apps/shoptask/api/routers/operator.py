from django.urls import path, include

from rest_framework.routers import DefaultRouter

from ..operator.purchase.views import OperatorPurchaseApiView
from ..operator.necessary.views import OperatorNecessaryApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('purchases', OperatorPurchaseApiView, basename='purchase')
router.register('necessaries', OperatorNecessaryApiView, basename='necessary')

app_name = 'shoptask'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
