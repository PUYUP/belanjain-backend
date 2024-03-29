from django.conf import settings
from django.db import models

def RequestExposerMiddleware(get_response):
    def middleware(request):
        models.request = request
        response = get_response(request)
        return response
    return middleware
