from uuid import uuid4
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import (
    Q, Prefetch, Case, When, Value, Sum, BooleanField, IntegerField)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils.timezone import localtime, now

from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.validators import check_uuid
from apps.shoptask.utils.permissions import IsCustomerOrReadOnly
from apps.shoptask.utils.constant import ALLOWED_DELETE_STATUS, DRAFT, ACCEPT

from .serializers import (
    PurchaseSerializer,
    PurchaseFactorySerializer,
    PurchaseSingleSerializer)

Purchase = get_model('shoptask', 'Purchase')
PurchaseDelivery = get_model('shoptask', 'PurchaseDelivery')
Necessary = get_model('shoptask', 'Necessary')
Goods = get_model('shoptask', 'Goods')
GoodsCatalog = get_model('shoptask', 'GoodsCatalog')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class PurchaseApiView(viewsets.ViewSet):
    """
    GET
    ------

    1. `status` ***[required]*** string with comma separate

    Params:

        {
            "status": "submitted,draft,reviewed,assigned,processed"
        }

    Return:

        [
            {
                "id": 54,
                "uuid": "8af36be2-d21e-474e-8cc0-67ff038d3959",
                "label": "Sharing modules",
                "schedule": "2020-05-17T11:29:27+07:00",
                "status": "submitted",
                "status_display": "Submitted",
                "url": "http://localhost:8000/api/shoptask/purchases/8af36be2-d21e-474e-8cc0-67ff038d3959/"
            }
            ...
        ]

    POST / UPDATE
    ------

    1. `label` ***[required]***
    2. `description` ***[optional]***
    3. `merchant` ***[optional]*** Shopping place reference
    4. `schedule` ***[required]***
    5. `shipping_address_uuid` ***[required]***

    Params:

        {
            "label": "Belanja Hari Raya",
            "description": "Persiapan lebaran",
            "merchant": "Minimarket 212",
            "schedule": "2020-05-20 21:32:43",
            "shipping_address_uuid": "e691f33d-615d-4a5d-b4af-f47a70b7c4ec"
        }

    If update ***status*** ex: from `draft` to `submitted` only accept param `status`

    Params:

        {
            "status": "submitted"
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
        status = self.request.query_params.get('status', None)

        # Single object
        if uuid:
            try:
                uuid = check_uuid(uid=uuid)
            except ValidationError as err:
                raise NotAcceptable(detail=_(' '.join(err.messages)))

            try:
                queryset = Purchase.objects \
                    .filter(uuid=uuid, customer_id=self.request.user.id) \
                    .annotate(
                        bill_summary=Sum(
                            'goods__bill', distinct=True,
                            output_field=IntegerField()
                        ),
                        has_operator=Case(
                            When(purchase_assigned__isnull=False, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        ),
                        has_delivery=Case(
                            When(purchase_delivery__isnull=False, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        ),
                        has_schedule=Case(
                            When(
                                Q(purchase_delivery__isnull=False)
                                & Q(purchase_delivery__schedule_date__isnull=False)
                                & Q(purchase_delivery__schedule_time_start__isnull=False)
                                & Q(purchase_delivery__schedule_time_end__isnull=False), 
                                then=Value(True)
                            ),
                            default=Value(False),
                            output_field=BooleanField()
                        )
                    ) \

                if is_update:
                    return queryset.select_for_update().get()
                return queryset.get()
            except ObjectDoesNotExist:
                raise NotFound()

        if not status:
            raise NotFound()

        # All objects
        return Purchase.objects.prefetch_related(Prefetch('customer')) \
            .select_related('customer') \
            .filter(customer_id=self.request.user.id, status__in=status.split(',')) \
            .order_by('-date_created')

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        response = dict()
        response['count'] = _PAGINATOR.count
        response['per_page'] = settings.PAGINATION_PER_PAGE
        response['navigate'] = {
            'offset': _PAGINATOR.offset,
            'limit': _PAGINATOR.limit,
            'previous': _PAGINATOR.get_previous_link(),
            'next': _PAGINATOR.get_next_link(),
        }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    # Alls
    def list(self, request, format=None):
        context = {'request': self.request}
        queryset = self.get_object()
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = PurchaseSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)

        # if 'status' is DRAFT and 'schedule_date' smaller than current date
        # set all 'schedule_*' to null
        if queryset.status == DRAFT:
            delivery = queryset.purchase_deliveries.first()
            datenow = localtime(now()).date()
            if delivery and delivery.schedule_date and (delivery.schedule_date < datenow):
                delivery.schedule_date = None
                delivery.schedule_time_start = None
                delivery.schedule_time_end = None
                delivery.save()
                queryset.refresh_from_db()

        serializer = PurchaseSingleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = PurchaseFactorySerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        # check permission
        self.check_object_permissions(self.request, queryset)

        serializer = PurchaseFactorySerializer(
            queryset, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
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

        queryset = Purchase.objects.filter(
            uuid=uuid, customer_id=request.user.id, status__in=ALLOWED_DELETE_STATUS)

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

    # Clone previous Purchase
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated],
            url_path='repurchase', url_name='repurchase')
    def repurchase(self, request, uuid=None):
        try:
            purchase = Purchase.objects.get(uuid=uuid, status=ACCEPT)
        except ObjectDoesNotExist:
            return Response({'detail': _("Not found")}, status=response_status.HTTP_404_NOT_FOUND)

        context = {'request': self.request}
        user = request.user

        purchase.pk = None
        purchase.uuid = uuid4()
        purchase.customer = user
        purchase.status = DRAFT
        purchase.save()

        # copy Necessary
        necessaries = Necessary.objects.filter(purchase__uuid=uuid)
        if necessaries.exists():
            necessaries_list_new = list()
            for item in necessaries:
                item.pk = None
                item.uuid = uuid4()
                item.customer = user
                item.purchase = purchase
                necessaries_list_new.append(item)

            if necessaries_list_new:
                Necessary.objects.bulk_create(necessaries_list_new)

        # get new Necessaries
        new_necessaries = Necessary.objects.filter(purchase__uuid=purchase.uuid)

        # copy Goods
        goods_by_necessary = defaultdict(list)
        goods = Goods.objects.filter(purchase__uuid=uuid)
        if goods.exists():
            for item in goods:
                necessary = item.necessary
                goods_by_necessary[necessary].append(item)

            goods_list_new = list()
            for index, item in enumerate(goods_by_necessary):
                new_necessary = new_necessaries[index]
                goods = goods_by_necessary[item]
                for g in goods:
                    g.pk = None
                    g.uuid = uuid4()
                    g.customer = user
                    g.purchase = purchase
                    g.necessary = new_necessary
                    g.price = None
                    g.bill = None
                    goods_list_new.append(g)

            if goods_list_new:
                Goods.objects.bulk_create(goods_list_new)

        # get new Goods
        new_goods = Goods.objects.filter(purchase__uuid=purchase.uuid)

        # copy GoodsCatalog
        catalogs_by_goods = defaultdict(list)
        goods_catalogs = GoodsCatalog.objects.filter(goods__purchase__uuid=uuid)
        if goods_catalogs.exists():
            for item in goods_catalogs:
                goods = item.goods
                catalogs_by_goods[goods].append(item)

            goods_catalogs_list_new = list()
            for item in catalogs_by_goods:
                ng = new_goods.get(label=item.label)
                catalogs = catalogs_by_goods[item]
                for c in catalogs:
                    c.pk = None
                    c.uuid = uuid4()
                    c.goods = ng
                    goods_catalogs_list_new.append(c)

            if goods_catalogs_list_new:
                GoodsCatalog.objects.bulk_create(goods_catalogs_list_new)

        # copy Delivery
        deliveries = PurchaseDelivery.objects.filter(purchase__uuid=uuid)
        if deliveries.exists():
            deliveries_new_list = list()
            for item in deliveries:
                item.pk = None
                item.uuid = uuid4()
                item.purchase = purchase
                item.schedule_date = None
                item.schedule_time_start = None
                item.schedule_time_end = None
                deliveries_new_list.append(item)
 
            if deliveries_new_list:
                PurchaseDelivery.objects.bulk_create(deliveries_new_list)

        # serializing
        serializer = PurchaseSingleSerializer(purchase, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_201_CREATED)
