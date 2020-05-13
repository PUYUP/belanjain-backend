from django.db import transaction

from rest_framework import serializers

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault

ShippingAddress = get_model('shoptask', 'ShippingAddress')


class ShippingAddressSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='shoptask:shipping_address-detail', lookup_field='uuid', read_only=True)

    class Meta:
        model = ShippingAddress
        fields = ('id', 'uuid', 'label', 'url', 'is_default',)


class ShippingAddressSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'


class ShippingAddressCreateSerializer(serializers.ModelSerializer):
    customer = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = ShippingAddress
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        obj = ShippingAddress.objects.create(**validated_data)
        return obj


class ShippingAddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

    @transaction.atomic
    def update(self, instance, validated_data):
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)
        instance.save()

        return instance
