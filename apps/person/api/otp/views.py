from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, NotAcceptable

from utils.generals import get_model
from apps.person.models.otp import _send_email

from .serializers import (
    OTPCodeListSerializer,
    OTPCodeCreateSerializer)

OTPCode = get_model('person', 'OTPCode')


class OTPCodeApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = OTPCodeCreateSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(''.join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Sub-action request password reset
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='resend', url_name='resend')
    def resend(self, request):
        """
        JSON Format:
        {
            "email": "string",
            "telephone": "string",
        }
        """
        email = request.data.get('email', None)
        telephone = request.data.get('telephone', None)

        if not email and not telephone:
            return Response(
                {'detail': _("Email or telephone must provided.")},
                status=response_status.HTTP_403_FORBIDDEN)

        if email and telephone:
            return Response(
                {'detail': _("Only accept one of email or telephone.")},
                status=response_status.HTTP_403_FORBIDDEN)

        try:
            otp = OTPCode.objects.get(email=email, is_used=False, is_expired=False)
        except ObjectDoesNotExist:
            return Response(
                {'detail': _("OTP not found.")},
                status=response_status.HTTP_404_NOT_FOUND)

        if email:
            _send_email(otp)

        return Response({'detail': _("Send!")}, status=response_status.HTTP_200_OK)

    # Sub-action request password reset
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='validate', url_name='validate')
    def validate(self, request):
        """
        JSON Format:
        {
            "email": "string",
            "telephone": "string",
            "otp_hash": "string",
            "otp_code": "string",
            "identifier": "string"
        }
        """
        email = request.data.get('email', None)
        telephone = request.data.get('telephone', None)
        identifier = request.data.get('identifier', None)
        otp_hash = request.data.get('otp_hash', None)
        otp_code = request.data.get('otp_code', None)

        if (not email and not telephone) or not identifier or not otp_hash or not otp_code:
            raise NotAcceptable(_("Required parameter not provided."
                                  "Required email or telephone, identifier, hash and code."))

        try:
            otp = OTPCode.objects.get(
                Q(email=email) & Q(identifier=identifier) & Q(otp_hash=otp_hash)
                | Q(otp_code=otp_code), Q(is_used=False), Q(is_expired=False))
        except ObjectDoesNotExist:
            raise NotFound()

        try:
            otp.validate(otp_code=otp_code)
        except ValidationError as e:
            return Response(
                {'detail': _(''.join(e.messages))},
                status=response_status.HTTP_403_FORBIDDEN)
        return Response({'detail': _("Passed!")}, status=response_status.HTTP_200_OK)
