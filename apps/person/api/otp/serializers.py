from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model

OTPCode = get_model('person', 'OTPCode')


class OTPCodeFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        data = kwargs.get('data', None)
        context = kwargs.get('context', None)

        email = data.get('email', None)
        telephone = data.get('telephone', None)
        request = context.get('request', None)

        if request.method == 'POST' and (not email or not telephone):
            if email:
                self.fields.pop('telephone')
            elif telephone:
                self.fields.pop('email')


class OTPCodeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPCode
        fields = ('email', 'telephone', 'otp_code', 'otp_hash',)


class OTPCodeFactorySerializer(OTPCodeFieldsModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = OTPCode
        fields = ('email', 'telephone', 'identifier', 'otp_hash',)
        read_only_fields = ('otp_hash',)
        extra_kwargs = {
            'identifier': {
                'required': True
            },
            'telephone': {
                'required': True,
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': True,
                'validators': [EmailValidator()]
            },
        }

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        instance = OTPCode(**attrs)
        instance.clean()
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop('email', None)
        telephone = validated_data.pop('telephone', None)
        identifier = validated_data.pop('identifier', None)

        if not email and not telephone:
            raise NotAcceptable(_("Email or telephone not provided."))

        _defaults = {
            'identifier': identifier,
            'is_used': False,
            'is_expired': False,
        }

        if email and not telephone:
            _defaults['email'] = email

        if telephone and not email:
            _defaults['telephone'] = telephone

        # Ops, please choose one (email or telehone)
        if telephone and email:
            raise NotAcceptable(_("Only accept one of email or telephone."))

        obj, _created = OTPCode.objects.get_or_create(**_defaults, defaults=_defaults)
        return obj
