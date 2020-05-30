from django.conf import settings
from django.db import transaction
from django.db.models import (
    Q, F, Prefetch, Case, When, Value, Count, Sum, BooleanField, IntegerField,
    CharField, Subquery, OuterRef)
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
from apps.shoptask.utils.permissions import (
    IsCustomerOrReadOnly, IsGoodsCustomerOrReject)
from apps.shoptask.utils.constant import ALLOWED_DELETE_STATUS, DONE, ACCEPT

from .serializers import (
    GoodsSerializer,
    GoodsFactorySerializer,
    GoodsSingleSerializer,
    GoodsAssignedFactorySerializer)

from ..purchase.serializers import PurchaseSingleSerializer
from ..necessary.serializers import NecessarySingleSerializer

Goods = get_model('shoptask', 'Goods')
GoodsCatalog = get_model('shoptask', 'GoodsCatalog')
GoodsAssigned = get_model('shoptask', 'GoodsAssigned')
Purchase = get_model('shoptask', 'Purchase')
Necessary = get_model('shoptask', 'Necessary')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()
_FINAL_STATUS = (DONE, ACCEPT,)


class GoodsApiView(viewsets.ViewSet):
    """
    GET
    ---------------------
    Return Goods from Customer based on Necessary

    Params:

        {
            "necessary_uuid": "valid UUID format uuid.uuid4"
        }
    
    Example:

    http://endpoint/?necessary_uuid=abfc-2252-ect

    Return list Goods:

        [
            {
                "id": 212,
                "uuid": "eaaf94e6-361e-4557-8bf1-fc3d5fd27035",
                "label": "Tempe kecil",
                "url": "http://localhost:8000/api/shoptask/goods/eaaf94e6-361e-4557-8bf1-fc3d5fd27035/",
                "is_done": false,
                "is_skip": false,
                "is_accept": false,
                "is_from_catalog": false,
                "quantity": 1,
                "metric": "piece",
                "metric_display": "Buah",
                "price": null,
                "description": "",
                "necessary": 89,
                "necessary_uuid": "926f50ce-ec3d-44e5-b85b-c926b0ae9568",
                "picture": null,
                "goods_catalogs": null
            },
            ...
        ]

    POST
    ---------------------
    Goods created with two options:

    1. Select from Catalog
    2. Manual input by Customer

    ---
    ### 1. From Catalog
    Params:

    1. `description` ***[optional]***
    2. `quantity` ***[required]***
    3. `metric` ***[required]*** slug for metric eg: ***kg***.
    4. `necessary_uuid` ***[required]***
    5. `catalog_uuid` ***[required]***

    ---

        {
            "description": "Some notes",
            "quantity": 4,
            "metric": "kg",
            "necessary_uuid": "c6ff7606-7ad4-4640-8bd1-5b158971361c",
            "catalog_uuid": "0fd8b1b2-eb51-4d41-9086-3d0688de8e8f"
        }

    ---
    ### 2. Manual
    Params:

    1. `label` ***[required]***
    2. `description` ***[optional]***
    3. `quantity` ***[required]***
    4. `metric` ***[required]*** slug for metric eg: ***kg***.
    5. `necessary_uuid` ***[required]***

    ---
        {
            "label": "My product name",
            "description": "Some notes",
            "quantity": 4,
            "metric": "kg",
            "necessary_uuid": "c6ff7606-7ad4-4640-8bd1-5b158971361c"
        }
    """
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
    def get_object(self, uuid=None, is_update=False):
        necessary_uuid = self.request.query_params.get('necessary_uuid', None)
        goods_catalog = GoodsCatalog.objects.filter(id=OuterRef('goods_catalog__id'))
        annotate_param = {
            'is_skip': Case(
                When(goods_assigned__is_skip=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            'is_done': Case(
                When(goods_assigned__is_done=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            'is_accept': Case(
                When(goods_assigned__is_accept=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            'is_from_catalog': Case(
                When(goods_catalog__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            'catalog_picture': Subquery(goods_catalog.values('catalog__pictures__value_image')[:1]),
            'goods_assigned_uuid': Case(
                When(goods_assigned__isnull=False, then=F('goods_assigned__uuid')),
                default=Value(None),
                output_field=CharField()
            )
        }

        queryset = Goods.objects \
            .prefetch_related(Prefetch('customer'), Prefetch('purchase'),
                              Prefetch('necessary'), Prefetch('goods_catalogs'),
                              Prefetch('goods_catalogs__catalog')) \
            .select_related('customer', 'purchase', 'necessary', 'goods_catalog',
                            'goods_catalog__catalog') \
            .annotate(**annotate_param)

        # Single object
        if uuid:
            try:
                uuid = check_uuid(uid=uuid)
            except ValidationError as err:
                raise NotAcceptable(detail=_(' '.join(err.messages)))

            try:
                if is_update:
                    return queryset.select_for_update().get(uuid=uuid, customer_id=self.request.user.id)
                return queryset.get(uuid=uuid, customer_id=self.request.user.id)
            except ObjectDoesNotExist:
                raise NotFound()

        if not necessary_uuid:
            raise NotFound()

        try:
            necessary_uuid = check_uuid(uid=necessary_uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))

        # All objects
        return queryset.filter(Q(customer_id=self.request.user.id), Q(necessary__uuid=necessary_uuid)) \
            .order_by('-date_created')

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        # purchase object
        necessary_uuid = self.request.query_params.get('necessary_uuid', None)
        try:
            necessary_uuid = check_uuid(uid=necessary_uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))

        context = {'request': self.request}
        purchase_obj = Purchase.objects.get(necessary__uuid=necessary_uuid)
        purchase_obj_serializer = PurchaseSingleSerializer(purchase_obj, many=False, context=context,
                                                           fields=('id', 'uuid', 'status_display', 'label',
                                                           'description', 'merchant', 'status'))

        necessary_annotate = {
            'bill_summary': Sum('goods__bill', output_field=IntegerField()),
            'total_count': Count('goods', distinct=False),
            'done_count': Sum(
                Case(
                    When(goods__goods_assigned__is_done=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            'skip_count': Sum(
                Case(
                    When(goods__goods_assigned__is_skip=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            'accept_count': Sum(
                Case(
                    When(goods__goods_assigned__is_accept=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
           'left_count': Sum(
                Case(
                    When(goods__goods_assigned__isnull=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        }

        necessary_obj = Necessary.objects \
            .prefetch_related(Prefetch('goods'), Prefetch('purchase')) \
            .select_related('purchase') \
            .filter(uuid=necessary_uuid) \
            .annotate(**necessary_annotate) \
            .first()
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
        serializer = GoodsFactorySerializer(data=request.data, context=context)
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
        queryset = self.get_object(uuid=uuid, is_update=True)

        # check permission
        self.check_object_permissions(self.request, queryset)

        serializer = GoodsFactorySerializer(
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
            # check permission
            self.check_object_permissions(self.request, queryset.first())

            queryset.delete()
            return Response(
                {'detail': _("Delete success!")},
                status=response_status.HTTP_204_NO_CONTENT)
        return NotAcceptable(_("Something wrong!"))


class GoodsAssignedApiView(viewsets.ViewSet):
    """Change `is_accept` by Customer
    To perform this action the Purchase status is DONE

    Param:

        {
            "is_accept": true
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'partial_update': [IsAuthenticated, IsGoodsCustomerOrReject],
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

    def list(self, request):
        return Response(status=response_status.HTTP_200_OK)

    # Update
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': self.request}

        try:
            queryset = GoodsAssigned.objects.select_for_update().get(uuid=uuid)
        except ObjectDoesNotExist:
            return Response(
                {'detail': _("Object invalid.")},
                status=response_status.HTTP_403_FORBIDDEN)

        # check permission
        self.check_object_permissions(self.request, queryset)

        serializer = GoodsAssignedFactorySerializer(
            queryset, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
