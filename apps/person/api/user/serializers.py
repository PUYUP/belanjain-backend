from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EmailValidator

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAcceptable

from pprint import pprint

# PROJECT UTILS
from utils.generals import get_model
from apps.person.utils.constant import REGISTER_VALIDATION

Profile = get_model('person', 'Profile')
Account = get_model('person', 'Account')
OTPCode = get_model('person', 'OTPCode')


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        try:
            fields = self.context['request'].query_params.get('fields')
        except KeyError:
            fields = None

        if fields:
            fields = fields.split(',')

            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


# Check duplicate email if has verified
class EmailDuplicateValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        serializer = serializer_field.parent
        data = getattr(serializer, 'initial_data', None)
        username = getattr(data, 'username', None)

        is_exist = User.objects \
            .prefetch_related('account') \
            .select_related('account') \
            .filter(email=value, account__email_verified=True) \
            .exists()

        if is_exist:
            raise serializers.ValidationError(_('Email has been used.'))


# Check email is validate
class EmailVerifiedValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        is_exist = OTPCode.objects.filter(
            identifier=REGISTER_VALIDATION, email=value, is_used=True) .exists()

        if not is_exist:
            raise serializers.ValidationError(_('Email not validated.'))


# Check duplicate telephone if has verified
class TelephoneDuplicateValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        serializer = serializer_field.parent
        data = getattr(serializer, 'initial_data', None)
        username = getattr(data, 'username', None)

        is_exist = User.objects \
            .prefetch_related('account') \
            .select_related('account') \
            .filter(account__telephone=value, account__telephone_verified=True) \
            .exists()

        if is_exist:
            raise serializers.ValidationError(_('Telephone has been used.'))


# Check telephone is validate
class TelephoneVerifiedValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        is_exist = OTPCode.objects.filter(
            identifier=REGISTER_VALIDATION, telephone=value, is_used=True).exists()

        if not is_exist:
            raise serializers.ValidationError(_('Telephone not validated.'))


# Check duplicate telephone if has verified
class TelephoneNumberValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value.isnumeric():
            raise serializers.ValidationError(_("Must be a number."))


# Password verification
class PasswordValidator(object):
    requires_context = True

    def __call__(self, value, serializer_field):
        validate_password(value)


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='person:user-detail', lookup_field='id', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'username', 'url',)


class SingleUserSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    biography = serializers.CharField(read_only=True, source='profile.biography')
    picture = serializers.ImageField(read_only=True, source='profile.picture')
    telephone = serializers.CharField(read_only=True, source='account.telephone')

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'biography', 'picture', 'telephone',)


class CreateUserSerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(required=False,
                                      validators=[TelephoneNumberValidator()],
                                      min_length=8, max_length=14)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'username',
                  'email', 'password', 'telephone',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 6,
                'validators': [PasswordValidator()]
            },
            'username': {
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'write_only': True,
                'required': False,
                'validators': [EmailValidator()]
            }
        }

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if settings.STRICT_TELEPHONE:
            self.fields['telephone'].required = True
            if settings.STRICT_TELEPHONE_DUPLICATE:
                self.fields['telephone'].validators += [TelephoneDuplicateValidator()]

            if settings.STRICT_TELEPHONE_VERIFIED:
                self.fields['telephone'].validators += [TelephoneVerifiedValidator()]

        if settings.STRICT_EMAIL:
            self.fields['email'].required = True
            if settings.STRICT_EMAIL_DUPLICATE:
                self.fields['email'].validators += [EmailDuplicateValidator()]

            if settings.STRICT_EMAIL_VERIFIED:
                self.fields['email'].validators += [EmailVerifiedValidator()]

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # always required
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)

        # depend on requirement
        first_name = validated_data.pop('first_name', None)
        telephone = validated_data.pop('telephone', None)

        user = User.objects.create_user(username, email, password)
        if settings.STRICT_EMAIL_VERIFIED:
            user.account.email_verified = True

        if settings.STRICT_TELEPHONE_VERIFIED:
            user.account.telephone_verified = True

        if telephone:
            user.account.telephone = telephone

        if (settings.STRICT_EMAIL_VERIFIED or settings.STRICT_TELEPHONE_VERIFIED
                or telephone):
            user.account.save()

        if first_name:
            user.first_name = first_name
            user.save()

        # must set if not return attribute error
        setattr(user, 'telephone', telephone)
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    biography = serializers.CharField(required=False)
    picture = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ('first_name', 'biography', 'picture',)

    @transaction.atomic
    def update(self, instance, validated_data):
        # to core user
        first_name = validated_data.pop('first_name', None)
        if first_name:
            instance.first_name = first_name
            instance.save()

        # to profile
        biography = validated_data.pop('biography', None)
        if biography:
            instance.profile.biography = biography
            instance.profile.save()

        return instance


class UpdateSecuritySerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(required=True)
    telephone = serializers.CharField(required=False,
                                      validators=[TelephoneNumberValidator()],
                                      min_length=8, max_length=14)

    class Meta:
        model = User
        fields = ('password', 'username', 'email', 'telephone', 'current_password',)
        extra_kwargs = {
            'password': {
                'write_only': True,
                'required': False,
                'min_length': 6,
                'validators': [PasswordValidator()]
            },
            'username': {
                'required': False,
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': False
            }
        }

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if settings.STRICT_TELEPHONE_DUPLICATE:
            self.fields['telephone'].validators += [TelephoneDuplicateValidator()]

        if settings.STRICT_TELEPHONE_VERIFIED:
            self.fields['telephone'].validators += [TelephoneVerifiedValidator()]

        if settings.STRICT_EMAIL_DUPLICATE:
            self.fields['email'].validators += [EmailDuplicateValidator()]

        if settings.STRICT_EMAIL_VERIFIED:
            self.fields['email'].validators += [EmailVerifiedValidator()]

    @transaction.atomic
    def update(self, instance, validated_data):
        account = getattr(instance, 'account', None)
        current_password = validated_data.pop('current_password', None)

        if not instance.check_password(current_password):
            raise serializers.ValidationError(_("Password invalid."))

        for key, value in validated_data.items():
            # extended user data (profile, account, other)
            if hasattr(account, key):
                old_value = getattr(account, key, None)
                if value and old_value != value:
                    setattr(account, key, value)
                    account.save()

            else:
                # core user data
                # change the password if changed
                if key == 'password' and not instance.check_password(value):
                    instance.set_password(value)
                    instance.save()
                else:
                    old_value = getattr(instance, key, None)
                    if value and old_value != value:
                        setattr(instance, key, value)
                        instance.save()
        return instance


class SecuritySerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(required=False, read_only=True,
                                      validators=[TelephoneNumberValidator()],
                                      min_length=8, max_length=14,
                                      source='account.telephone')

    class Meta:
        model = User
        fields = ('username', 'email', 'telephone',)
        extra_kwargs = {
            'password': {
                'read_only': True
            },
            'username': {
                'read_only': True
            },
            'email': {
                'read_only': True
            }
        }
