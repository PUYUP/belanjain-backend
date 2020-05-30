from django.urls import path, include

from .views import RootApiView

from apps.person.api import routers as person_routers
from apps.shoptask.api.routers import (
    customer as customer_routers, operator as operator_routers)

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('person/', include((person_routers, 'person'), namespace='person')),
    path('customer/', include((customer_routers, 'shoptask'), namespace='customer')),
    path('operator/', include((operator_routers, 'shoptask'), namespace='operator')),
]
