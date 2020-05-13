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

Purchase = get_model('shoptask', 'Purchase')
PurchaseShipping = get_model('shoptask', 'PurchaseShipping')
PurchaseAssigned = get_model('shoptask', 'PurchaseAssigned')


class PurchaseAssignedSerializer(serializers.ModelSerializer):
    operator = SingleUserSerializer(many=False, read_only=True)
    class Meta:
        model = PurchaseAssigned
        fields = '__all__'


class PurchaseShippingSerializer(serializers.ModelSerializer):
    shipping_to = ShippingAddressSingleSerializer(many=False)

    class Meta:
        model = PurchaseShipping
        fields = '__all__'


class PurchaseShippingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseShipping
        fields = '__all__'
        extra_kwargs = {'purchase': {'read_only': True}}


class PurchaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='shoptask:purchase-detail', lookup_field='uuid',
        read_only=True)

    class Meta:
        model = Purchase
        fields = ('id', 'uuid', 'label', 'schedule', 'status', 'status_display', 'url',)


class PurchaseSingleSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    has_operator = serializers.BooleanField(read_only=True)
    has_shipping = serializers.BooleanField(read_only=True)
    purchase_shippings = PurchaseShippingSerializer(many=True, read_only=True)
    purchase_assigneds = PurchaseAssignedSerializer(many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'


class PurchaseSinglePlainSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    has_operator = serializers.BooleanField(read_only=True)
    has_shipping = serializers.BooleanField(read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'


class PurchaseCreateSerializer(serializers.ModelSerializer):
    customer = serializers.HiddenField(default=CurrentUserDefault())
    purchase_shippings = PurchaseShippingCreateSerializer(many=True)

    # just a placeholder after object created
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        purchase_shippings = validated_data.pop('purchase_shippings', None)
        status = validated_data.pop('status', None) # prevent user fill status
        obj = Purchase.objects.create(**validated_data, status=DRAFT)

        if obj and purchase_shippings:
            shippings = list()
            for item in purchase_shippings:
                shipping_to = item.get('shipping_to', None)
                if shipping_to:
                    shipping = PurchaseShipping(purchase=obj, shipping_to=shipping_to)
                    shippings.append(shipping)

            if shippings:
                PurchaseShipping.objects.bulk_create(shippings)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        purchase_shippings = validated_data.pop('purchase_shippings', None)
        purchase_assigneds = validated_data.pop('purchase_assigneds', None)

        # restrict update status
        status = validated_data.get('status', None)
        if status and status not in [DRAFT, SUBMITTED]:
            raise NotAcceptable(_("You can't perform this action."))

        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        # update or create related object
        if purchase_shippings:
            current_shippings = instance.purchase_shippings.all()
            shippings = list()

            for item in purchase_shippings:
                shipping_to = item.get('shipping_to', None)
                if shipping_to:
                    if current_shippings:
                        current_shippings.update(shipping_to=shipping_to)
                    else:
                        shipping = PurchaseShipping(purchase=instance, shipping_to=shipping_to)
                        shippings.append(shipping)

            if shippings:
                PurchaseShipping.objects.bulk_create(shippings)

        instance.save()
        return instance
