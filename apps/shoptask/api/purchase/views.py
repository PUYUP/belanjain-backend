from django.conf import settings
from django.db import transaction
from django.db.models import Q, Prefetch, Case, When, Value, BooleanField
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
    PurchaseSerializer,
    PurchaseCreateSerializer,
    PurchaseSingleSerializer)

Purchase = get_model('shoptask', 'Purchase')

# Define to avoid used ...().paginate__
_PAGINATOR = PageNumberPagination()


class PurchaseApiView(viewsets.ViewSet):
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
        status = self.request.query_params.get('status', None)

        # Single object
        if uuid:
            try:
                uuid = check_uuid(uid=uuid)
            except ValidationError as err:
                raise NotAcceptable(detail=_(' '.join(err.messages)))

            try:
                return Purchase.objects \
                    .annotate(
                        has_operator=Case(
                            When(purchase_assigned__isnull=False, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        ),
                        has_shipping=Case(
                            When(purchase_shipping__isnull=False, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        )
                    ) \
                    .get(uuid=uuid, customer_id=self.request.user.id)
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
        serializer = PurchaseSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = PurchaseSingleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = PurchaseCreateSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': self.request}

        queryset = self.get_object(uuid=uuid)
        serializer = PurchaseCreateSerializer(
            queryset, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            serializer_single = PurchaseSingleSerializer(queryset, many=False, context=context)
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

        queryset = Purchase.objects.filter(
            uuid=uuid, customer_id=request.user.id, status__in=ALLOWED_DELETE_STATUS)

        if not queryset.exists():
            return NotAcceptable(_("Action rejected. Delete failed!"))

        if queryset.exists():
            queryset.delete()
            return Response(
                {'detail': _("Delete success!")},
                status=response_status.HTTP_204_NO_CONTENT)
        return NotAcceptable(_("Something wrong!"))