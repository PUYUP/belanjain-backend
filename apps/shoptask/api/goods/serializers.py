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

Goods = get_model('shoptask', 'Goods')


class GoodsSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='shoptask:goods-detail', lookup_field='uuid',
        read_only=True)
    is_done = serializers.BooleanField(read_only=True)
    is_skip = serializers.BooleanField(read_only=True)
    is_accept = serializers.BooleanField(read_only=True)
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = Goods
        fields = ('id', 'uuid', 'label', 'url', 'is_done', 'is_skip', 'is_accept',
                  'quantity', 'metric', 'metric_display', 'price', 'description',
                  'necessary',)


class GoodsSingleSerializer(serializers.ModelSerializer):
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = Goods
        fields = '__all__'


class GoodsCreateSerializer(serializers.ModelSerializer):
    customer = serializers.HiddenField(default=CurrentUserDefault())
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = Goods
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        obj = Goods.objects.create(**validated_data)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        instance.save()
        return instance
