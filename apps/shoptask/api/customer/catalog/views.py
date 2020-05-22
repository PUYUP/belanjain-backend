from django.conf import settings
from django.db import transaction
from django.db.models import (
    Q, F, Prefetch, Case, When, Value, Count, Sum, BooleanField, IntegerField,
    CharField, IntegerField, Subquery, OuterRef, Exists)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.validators import check_uuid
from apps.shoptask.utils.constant import PUBLISH

from .serializers import CatalogSerializer, CatalogSingleSerializer
from apps.shoptask.api.customer.necessary.serializers import NecessarySingleSerializer

Catalog = get_model('shoptask', 'Catalog')
Goods = get_model('shoptask', 'Goods')
Necessary = get_model('shoptask', 'Necessary')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


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
        category_uuid = self.request.query_params.get('category_uuid', None)
        brand_uuid = self.request.query_params.get('brand_uuid', None)
        keyword = self.request.query_params.get('keyword', None)

        user = self.request.user

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

        queryset = Catalog.objects.prefetch_related(Prefetch('category'), Prefetch('brand'), Prefetch('pictures')) \
            .select_related('category', 'brand') \
            .filter(status=PUBLISH) \
            .exclude(
                Q(goods_catalog__goods__necessary__isnull=False),
                Q(goods_catalog__goods__necessary__customer_id=self.request.user.id)) \
            .order_by('label')

        if category_uuid:
            queryset = queryset.filter(category__uuid=category_uuid)

        if brand_uuid:
            queryset = queryset.filter(brand__uuid=brand_uuid)

        if keyword:
            queryset = queryset.filter(label__icontains=keyword)

        return queryset

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        # purchase object
        context = {'request': self.request}
        necessary_uuid = self.request.query_params.get('necessary_uuid', None)
   
        necessary_obj = Necessary.objects.get(uuid=necessary_uuid)
        necessary_obj_serializer = NecessarySingleSerializer(necessary_obj, many=False, context=context)

        response = dict()
        response['count'] = _PAGINATOR.count
        response['per_page'] = settings.PAGINATION_PER_PAGE
        response['navigate'] = {
            'offset': _PAGINATOR.offset,
            'limit': _PAGINATOR.limit,
            'previous': _PAGINATOR.get_previous_link(),
            'next': _PAGINATOR.get_next_link(),
        }
        response['necessary'] = necessary_obj_serializer.data
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
