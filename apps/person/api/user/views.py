from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email

# THIRD PARTY
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.pagination import LimitOffsetPagination

# JWT
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView)

# SERIALIZERS
from .serializers import (
    UserSerializer,
    SingleUserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
    UpdateSecuritySerializer,
    SecuritySerializer)

# GET MODELS FROM GLOBAL UTILS
from utils.generals import get_model
from apps.person.utils.permissions import IsUserSelfOrReject

Account = get_model('person', 'Account')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class UserApiView(viewsets.ViewSet):
    """
    {
        "username": "Sulis",
        "telephone": "095252653",
        "email": "admin@email.com",
        "password": "0353##$fs"
    }
    """
    lookup_field = 'id'
    permission_classes = (AllowAny,)
    permission_action = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsUserSelfOrReject],
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
    def get_object(self, id=None, is_update=False):
        # Single object
        if id:
            try:
                queryset = User.objects
                if is_update:
                    return queryset.select_for_update().get(id=id)
                return queryset.get(id=id)
            except ObjectDoesNotExist:
                raise NotFound()

        # All objects
        return User.objects.prefetch_related(Prefetch('account'), Prefetch('profile')) \
            .select_related('account', 'profile') \
            .all()

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

    # All Users
    def list(self, request, format=None):
        context = {'request': self.request}
        queryset = self.get_object()
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = UserSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single User
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, id=None, format=None):
        context = {'request': self.request}
        queryset = self.get_object(id=id)
        serializer = SingleUserSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Register User
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': self.request}
        serializer = CreateUserSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update basic user data
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, id=None, format=None):
        context = {'request': self.request}

        # Single object
        instance = self.get_object(id=id, is_update=True)

        # Append file
        if request.FILES:
            setattr(request.data, 'files', request.FILES)

        serializer = UpdateUserSerializer(
            instance, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            serializer_single = SingleUserSerializer(instance, many=False, context=context)
            return Response(serializer_single.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Sub-action check email available
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='check-email', url_name='view_check_email')
    def view_check_email(self, request):
        """
        {
            "email": "my@email.com"
        }
        """
        data = request.data
        email = data.get('email', None)
        if not email:
            raise NotFound(_("Email not provided."))

        try:
            validate_email(email)
        except ValidationError as e:
            raise NotAcceptable(_(''.join(e.messages)))

        try:
            Account.objects.get(email=email, email_verified=True)
            raise NotAcceptable(_("Email has used."))
        except ObjectDoesNotExist:
            return Response({'detail': _("Passed!")}, status=response_status.HTTP_200_OK)

    # Sub-action check telephone available
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='check-telephone', url_name='view_check_telephone')
    def view_check_telephone(self, request):
        """
        {
            "telephone": "1234567890"
        }
        """
        data = request.data
        telephone = data.get('telephone', None)
        if not telephone:
            raise NotFound(_("Telephone not provided."))

        try:
            Account.objects.get(telephone=telephone, telephone_verified=True)
            raise NotAcceptable(_("Telephone has used."))
        except ObjectDoesNotExist:
            return Response({'detail': _("Passed!")}, status=response_status.HTTP_200_OK)

    # Sub-action logout!
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated, IsUserSelfOrReject],
            url_path='logout', url_name='view_logout')
    def view_logout(self, request, id=None):
        logout(request)
        return Response({'detail': _("Logout!")}, status=response_status.HTTP_204_NO_CONTENT)

    # Sub-action secret zone
    @method_decorator(never_cache)
    @transaction.atomic
    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAuthenticated, IsUserSelfOrReject],
            url_path='security', url_name='view_security')
    def view_security(self, request, id=None):
        context = {'request': self.request}
        queryset = self.get_object(id=id)

        if request.method == 'PATCH':
            serializer = UpdateSecuritySerializer(
                queryset, data=request.data, partial=True, context=context)

            if serializer.is_valid():
                serializer.save()
                return Response({'detail': _("Passed!")}, status=response_status.HTTP_200_OK)

        if request.method == 'GET':
            serializer = SecuritySerializer(queryset, many=False, context=context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)

        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)


class TokenObtainPairSerializerExtend(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user:
            data['id'] = self.user.id
            data['username'] = self.user.username
            data['first_name'] = self.user.first_name
        return data


class TokenObtainPairViewExtend(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializerExtend

    @method_decorator(never_cache)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # Make user logged-in
        if settings.LOGIN_WITH_JWT:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

        return Response(serializer.validated_data, status=response_status.HTTP_200_OK)
