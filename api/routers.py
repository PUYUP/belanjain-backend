from django.urls import path, include

from .views import RootApiView

from apps.person.api import routers as person_routers
from apps.shoptask.api import routers as shoptask_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('person/', include((person_routers, 'person'), namespace='persons')),
    path('shoptask/', include((shoptask_routers, 'shoptask'), namespace='shoptasks')),
]
