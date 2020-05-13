from django.conf import settings
from django.db import transaction
from django.db.models import (
    Q, F, Prefetch, Case, When, Value, Count, Sum, BooleanField, IntegerField)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from utils.generals import get_model
from utils.validators import check_uuid
from apps.shoptask.utils.constant import PUBLISH

from .serializers import CatalogSerializer, CatalogSingleSerializer

Catalog = get_model('shoptask', 'Catalog')

# Define to avoid used ...().paginate__
_PAGINATOR = PageNumberPagination()


class CatalogApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action
                    [self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    # Get a objects
    def get_object(self, uuid=None):
        purchase_uuid = self.request.query_params.get('purchase_uuid', None)
        necessary_uuid = self.request.query_params.get('necessary_uuid', None)

        # Single object
        if uuid:
            try:
                uuid = check_uuid(uid=uuid)
            except ValidationError as err:
                raise NotAcceptable(detail=_(' '.join(err.messages)))

            try:
                return Catalog.objects.get(uuid=uuid)
            except ObjectDoesNotExist:
                raise NotFound()

        # All objects
        return Catalog.objects.prefetch_related(Prefetch('category'), Prefetch('pictures')) \
            .select_related('category') \
            .filter(status=PUBLISH) \
            .annotate(
                is_selected=Case(
                    When(goods_catalog__goods__necessary__uuid=necessary_uuid, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ) \
            .exclude(Q(goods_catalog__goods__necessary__isnull=False),
                     Q(goods_catalog__goods__necessary__customer_id=self.request.user.id),
                     ~Q(goods_catalog__goods__necessary__uuid=necessary_uuid)) \
            .order_by('-label')

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        previous_page = None
        next_page = None

        if _PAGINATOR.page.has_previous():
            previous_page = _PAGINATOR.page.previous_page_number()
    
        if _PAGINATOR.page.has_next():
            next_page = _PAGINATOR.page.next_page_number()

        response = dict()
        response['count'] = _PAGINATOR.page.paginator.count
        response['per_page'] = settings.PAGINATION_PER_PAGE
        response['navigate'] = {
            'previous': _PAGINATOR.get_previous_link(),
            'next': _PAGINATOR.get_next_link(),
            'previous_page':  previous_page,
            'next_page': next_page
        }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    # Alls
    def list(self, request, format=None):
        context = {'request': self.request}
        queryset = self.get_object()
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = CatalogSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = CatalogSingleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
