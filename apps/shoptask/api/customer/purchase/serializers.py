from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault
from apps.shoptask.utils.constant import DRAFT, SUBMITTED

from apps.shoptask.api.customer.shipping.serializers import ShippingAddressSingleSerializer
from apps.person.api.user.serializers import SingleUserSerializer

Purchase = get_model('shoptask', 'Purchase')
PurchaseShipping = get_model('shoptask', 'PurchaseShipping')
PurchaseAssigned = get_model('shoptask', 'PurchaseAssigned')
ShippingAddress = get_model('shoptask', 'ShippingAddress')


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
    shipping = PurchaseShippingSerializer(many=False, read_only=True)
    assigned = PurchaseAssignedSerializer(many=False, read_only=True)

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
    shipping_address_uuid = serializers.UUIDField(write_only=True)

    # just a placeholder after object created
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # restrict update status
        # customer allow only change to DRAFT and SUBMITTED
        status = data.get('status', None)
        if status and status not in [DRAFT, SUBMITTED]:
            raise serializers.ValidationError({'status': _("You can't perform this action.")})

        # prepare shipping address
        shipping_address_uuid = data.pop('shipping_address_uuid', None)
        if shipping_address_uuid:
            try:
                shipping_address = ShippingAddress.objects.get(uuid=shipping_address_uuid)
                data['shipping_address'] = shipping_address
            except ObjectDoesNotExist:
                raise serializers.ValidationError({'shipping_address': _("Invalid.")})
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        shipping_address = validated_data.pop('shipping_address', None)
        status = validated_data.pop('status', None) # prevent user fill status
        obj = Purchase.objects.create(**validated_data, status=DRAFT)

        if obj and shipping_address:
            PurchaseShipping.objects.create(purchase=obj, shipping_to=shipping_address)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        # get and remove object
        shipping_address = validated_data.pop('shipping_address', None)

        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        # update or create shipping
        if shipping_address:
            current_shippings = instance.purchase_shippings \
                .prefetch_related(Prefetch('purchase'), Prefetch('shipping_to')) \
                .select_related('purchase', 'shipping_to') \
                .all()
            if current_shippings:
                current_shippings.update(shipping_to=shipping_address)
            else:
                PurchaseShipping.objects.create(purchase=instance, shipping_to=shipping_address)

        instance.save()
        return instance
