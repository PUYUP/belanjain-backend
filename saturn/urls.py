from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from api import routers as api_routers

# Sentry verification
def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('api/', include(api_routers)),
    path('admin/', admin.site.urls),
    path('sentry-debug/', trigger_error),
]

# Change adminstration label
admin.site.site_header = 'Administrator'
admin.site.site_title = 'Administrator'
admin.site.index_title = 'Welcome'

urlpatterns += static(settings.MEDIA_URL,
                      document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL,
                      document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)