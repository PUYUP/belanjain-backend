from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault
from apps.shoptask.utils.constant import DRAFT, SUBMITTED

from apps.shoptask.api.shipping.serializers import ShippingAddressSingleSerializer
from apps.person.api.user.serializers import SingleUserSerializer

Necessary = get_model('shoptask', 'Necessary')


class NecessarySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='shoptask:necessary-detail', lookup_field='uuid',
        read_only=True)
    total_count = serializers.IntegerField(read_only=True)
    done_count = serializers.IntegerField(read_only=True)
    skip_count = serializers.IntegerField(read_only=True)
    accept_count = serializers.IntegerField(read_only=True)
    left_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Necessary
        fields = ('id', 'uuid', 'label', 'url', 'total_count', 'done_count',
                  'skip_count', 'accept_count', 'left_count',)


class NecessarySingleSerializer(serializers.ModelSerializer):
    total_count = serializers.IntegerField(read_only=True)
    done_count = serializers.IntegerField(read_only=True)
    skip_count = serializers.IntegerField(read_only=True)
    accept_count = serializers.IntegerField(read_only=True)
    left_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Necessary
        fields = '__all__'


class NecessaryCreateSerializer(serializers.ModelSerializer):
    customer = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Necessary
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        obj = Necessary.objects.create(**validated_data)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        instance.save()
        return instance
