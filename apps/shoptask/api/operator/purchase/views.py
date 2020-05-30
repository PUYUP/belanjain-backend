from django.conf import settings
from django.db import transaction
from django.db.models import (
    Q, Prefetch, Case, When, Value, Sum, BooleanField, IntegerField)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.validators import check_uuid
from apps.shoptask.utils.permissions import IsOperatorOrReject

from .serializers import (
    OperatorPurchaseSerializer,
    OperatorPurchaseFactorySerializer,
    OperatorPurchaseSingleSerializer)

Purchase = get_model('shoptask', 'Purchase')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class OperatorPurchaseApiView(viewsets.ViewSet):
    """ Get Purchase assigned to Operator

    GET
    ------

    Accept params;

    1. `status` ***[required]*** string with comma separate

    JSON;

        {
            "status": "assigned,processed"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsOperatorOrReject],
        'destroy': [IsAuthenticated, IsOperatorOrReject],
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action[self.action]]
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
                    .filter(uuid=uuid, purchase_assigned__operator_id=self.request.user.id) \
                    .annotate(
                        bill_summary=Sum(
                            'goods__bill', distinct=True,
                            output_field=IntegerField()
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
            .filter(purchase_assigned__operator_id=self.request.user.id,
                    status__in=status.split(',')) \
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
        serializer = OperatorPurchaseSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = OperatorPurchaseSingleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Update
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        # check permission
        self.check_object_permissions(self.request, queryset)

        serializer = OperatorPurchaseFactorySerializer(
            queryset, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)