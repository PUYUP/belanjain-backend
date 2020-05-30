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
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.validators import check_uuid
from apps.shoptask.utils.permissions import IsOperatorOrReject
from apps.shoptask.utils.constant import ALLOWED_DELETE_STATUS

from .serializers import (
    OperatorNecessarySerializer,
    OperatorNecessaryFactorySerializer,
    OperatorNecessarySingleSerializer)

Necessary = get_model('shoptask', 'Necessary')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class OperatorNecessaryApiView(viewsets.ViewSet):
    """
    GET
    ------
    
    1. `purchase_uuid` ***[required]***

    Params:

        {
            "purchase_uuid": "5039d278-503b-421e-baa1-b70629153e6d"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsOperatorOrReject],
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
        purchase_uuid = self.request.query_params.get('purchase_uuid', None)
        annotate = {
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

        # Single object
        if uuid:
            try:
                uuid = check_uuid(uid=uuid)
            except ValidationError as err:
                raise NotAcceptable(detail=_(' '.join(err.messages)))

            try:
                queryset = Necessary.objects.annotate(**annotate)
                if is_update:
                    return queryset.select_for_update() \
                        .get(uuid=uuid, customer_id=self.request.user.id)
                return queryset.get(uuid=uuid, customer_id=self.request.user.id)
            except ObjectDoesNotExist:
                raise NotFound()

        if not purchase_uuid:
            raise NotFound()

        try:
            purchase_uuid = check_uuid(uid=purchase_uuid)
        except ValidationError as err:
            raise NotAcceptable(detail=_(' '.join(err.messages)))

        # All objects
        return Necessary.objects.prefetch_related(Prefetch('customer'), Prefetch('purchase')) \
            .select_related('customer', 'purchase') \
            .filter(purchase__purchase_assigned__operator_id=self.request.user.id, purchase__uuid=purchase_uuid) \
            .annotate(**annotate) \
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
        serializer = OperatorNecessarySerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = OperatorNecessarySingleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Update
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        # check permission
        self.check_object_permissions(self.request, queryset)

        serializer = OperatorNecessaryFactorySerializer(
            queryset, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            serializer_single = OperatorNecessarySingleSerializer(queryset, many=False, context=context)
            return Response(serializer_single.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
