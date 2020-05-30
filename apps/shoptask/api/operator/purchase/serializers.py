from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault
from apps.shoptask.utils.constant import DRAFT, SUBMITTED, ACCEPT, DONE, PROCESSED

from apps.shoptask.api.customer.shipping.serializers import ShippingAddressSingleSerializer
from apps.person.api.user.serializers import SingleUserSerializer

Purchase = get_model('shoptask', 'Purchase')
PurchaseDelivery = get_model('shoptask', 'PurchaseDelivery')
PurchaseAssigned = get_model('shoptask', 'PurchaseAssigned')
ShippingAddress = get_model('shoptask', 'ShippingAddress')


class OperatorPurchaseDeliverySerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSingleSerializer(many=False)

    class Meta:
        model = PurchaseDelivery
        fields = '__all__'


class OperatorPurchaseDeliveryFactorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDelivery
        fields = '__all__'
        extra_kwargs = {'purchase': {'read_only': True}}


class OperatorPurchaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='operator:purchase-detail', lookup_field='uuid',
        read_only=True)

    class Meta:
        model = Purchase
        fields = ('id', 'uuid', 'label', 'status', 'status_display', 'url',)


class OperatorPurchaseSingleSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display',
                                           read_only=True)
    bill_summary = serializers.IntegerField(read_only=True)
    shipping = OperatorPurchaseDeliverySerializer(many=False, read_only=True)
    customer = SingleUserSerializer(many=False, read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class OperatorPurchaseFactorySerializer(serializers.ModelSerializer):
    # just a placeholder after object created
    status_display = serializers.CharField(source='get_status_display',
                                           read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # If update has instance
        instance = getattr(self, 'instance', None)

        # restrict update status
        # Operator allow only change to DONE
        status = data.get('status', None)
        if status and status not in [DONE]:
            raise serializers.ValidationError({'status': _("You can't perform this action.")})

        # update to DONE must after PROCESSED
        if instance and status == DONE:
            if instance.status != PROCESSED:
                raise serializers.ValidationError({'status': _("Purchase isn't processed yet.")})
            data['status'] = DONE
        return data

    def to_representation(self, instance):
        """
        Serialize Purchase instances using a Purchase serializer,
        and note instances using a note serializer.
        """
        if isinstance(instance, Purchase):
            serializer = OperatorPurchaseSingleSerializer(instance, many=False, context=self.context)
        else:
            raise Exception(_("Unexpected type of object."))

        data = serializer.data
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        instance.save()
        return instance
