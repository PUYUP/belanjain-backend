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
from apps.shoptask.utils.permissions import IsCustomerOrReadOnly
from apps.shoptask.utils.constant import ALLOWED_DELETE_STATUS

from .serializers import (
    GoodsSerializer,
    GoodsCreateSerializer,
    GoodsSingleSerializer)

from ..purchase.serializers import PurchaseSinglePlainSerializer
from ..necessary.serializers import NecessarySingleSerializer

Goods = get_model('shoptask', 'Goods')
Purchase = get_model('shoptask', 'Purchase')
Necessary = get_model('shoptask', 'Necessary')

# Define to avoid used ...().paginate__
_PAGINATOR = PageNumberPagination()


class GoodsApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsCustomerOrReadOnly],
        'destroy': [IsAuthenticated, IsCustomerOrReadOnly],
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
        necessary_uuid = self.request.query_params.get('necessary_uuid', None)

        # Single object
        if uuid:
            try:
                uuid = check_uuid(uid=uuid)
            except ValidationError as err:
                raise NotAcceptable(detail=_(' '.join(err.messages)))

            try:
                return Goods.objects.get(uuid=uuid, customer_id=self.request.user.id)
            except ObjectDoesNotExist:
                raise NotFound()

        if not necessary_uuid:
            raise NotFound()

        try:
            necessary_uuid = check_uuid(uid=necessary_uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))

        # All objects
        return Goods.objects.prefetch_related(Prefetch('customer'), Prefetch('purchase'), Prefetch('necessary')) \
            .annotate(
                is_skip=Case(
                    When(goods_assigned__is_skip=True, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                ),
                is_done=Case(
                    When(goods_assigned__is_done=True, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                ),
                is_accept=Case(
                    When(goods_assigned__is_accept=True, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                ),
            ) \
            .select_related('customer', 'purchase', 'necessary') \
            .filter(Q(customer_id=self.request.user.id), Q(necessary__uuid=necessary_uuid)) \
            .order_by('-date_created')

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        previous_page = None
        next_page = None

        if _PAGINATOR.page.has_previous():
            previous_page = _PAGINATOR.page.previous_page_number()
    
        if _PAGINATOR.page.has_next():
            next_page = _PAGINATOR.page.next_page_number()

        # purchase object
        necessary_uuid = self.request.query_params.get('necessary_uuid', None)
        try:
            necessary_uuid = check_uuid(uid=necessary_uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))

        context = {'request': self.request}
        purchase_obj = Purchase.objects.get(necessary__uuid=necessary_uuid)
        purchase_obj_serializer = PurchaseSinglePlainSerializer(purchase_obj, many=False, context=context)

        necessary_obj = Necessary.objects.get(uuid=necessary_uuid)
        necessary_obj_serializer = NecessarySingleSerializer(necessary_obj, many=False, context=context)

        response = dict()
        response['count'] = _PAGINATOR.page.paginator.count
        response['per_page'] = settings.PAGINATION_PER_PAGE
        response['navigate'] = {
            'previous': _PAGINATOR.get_previous_link(),
            'next': _PAGINATOR.get_next_link(),
            'previous_page':  previous_page,
            'next_page': next_page
        }
        response['purchase'] = purchase_obj_serializer.data
        response['necessary'] = necessary_obj_serializer.data
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    # Alls
    def list(self, request, format=None):
        context = {'request': self.request}
        queryset = self.get_object()
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = GoodsSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = GoodsSingleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = GoodsCreateSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            queryset = self.get_object(uuid=serializer.data['uuid'])
            serializer_single = GoodsSingleSerializer(queryset, many=False, context=context)
            return Response(serializer_single.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': self.request}

        queryset = self.get_object(uuid=uuid)
        serializer = GoodsCreateSerializer(
            queryset, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            serializer_single = GoodsSingleSerializer(queryset, many=False, context=context)
            return Response(serializer_single.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Delete
    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        context = {'request': self.request}

        try:
            uuid = check_uuid(uid=uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))

        queryset = Goods.objects \
            .filter(uuid=uuid, customer_id=request.user.id,
                    purchase__status__in=ALLOWED_DELETE_STATUS)

        if not queryset.exists():
            return NotAcceptable(_("Action rejected. Delete failed!"))

        if queryset.exists():
            queryset.delete()
            return Response(
                {'detail': _("Delete success!")},
                status=response_status.HTTP_204_NO_CONTENT)
        return NotAcceptable(_("Something wrong!"))
