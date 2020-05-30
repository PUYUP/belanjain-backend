from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault
from apps.shoptask.utils.constant import DRAFT, SUBMITTED, ACCEPT, DONE

from ..base.serializers import DynamicFieldsModelSerializer
from apps.shoptask.api.customer.shipping.serializers import ShippingAddressSingleSerializer
from apps.person.api.user.serializers import SingleUserSerializer

Purchase = get_model('shoptask', 'Purchase')
PurchaseDelivery = get_model('shoptask', 'PurchaseDelivery')
PurchaseAssigned = get_model('shoptask', 'PurchaseAssigned')
ShippingAddress = get_model('shoptask', 'ShippingAddress')


class PurchaseAssignedSerializer(serializers.ModelSerializer):
    operator = SingleUserSerializer(many=False, read_only=True)

    class Meta:
        model = PurchaseAssigned
        fields = '__all__'


class PurchaseDeliverySerializer(serializers.ModelSerializer):
    shipping_address = ShippingAddressSingleSerializer(many=False)

    class Meta:
        model = PurchaseDelivery
        fields = '__all__'


class PurchaseDeliveryFactorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDelivery
        fields = '__all__'
        extra_kwargs = {'purchase': {'read_only': True}}


class PurchaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='customer:purchase-detail', lookup_field='uuid',
        read_only=True)

    class Meta:
        model = Purchase
        fields = ('id', 'uuid', 'label', 'status', 'status_display', 'url',)


class PurchaseSingleSerializer(DynamicFieldsModelSerializer):
    status_display = serializers.CharField(source='get_status_display',
                                           read_only=True)
    has_operator = serializers.BooleanField(read_only=True)
    has_delivery = serializers.BooleanField(read_only=True)
    has_schedule = serializers.BooleanField(read_only=True)
    bill_summary = serializers.IntegerField(read_only=True)
    shipping = PurchaseDeliverySerializer(many=False, read_only=True)
    assigned = PurchaseAssignedSerializer(many=False, read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not getattr(data, 'has_delivery', None):
            data['has_delivery'] = instance.purchase_deliveries.exists()

        if not getattr(data, 'has_schedule', None):
            data['has_schedule'] = instance.purchase_deliveries \
                .filter(schedule_date__isnull=False,
                        schedule_time_start__isnull=False,
                        schedule_time_end__isnull=False) \
                .exists()
        return data


class PurchaseFactorySerializer(serializers.ModelSerializer):
    customer = serializers.HiddenField(default=CurrentUserDefault())
    shipping_address_uuid = serializers.UUIDField(write_only=True)
    schedule_date = serializers.DateField(write_only=True)
    schedule_time_start = serializers.TimeField(write_only=True)
    schedule_time_end = serializers.TimeField(write_only=True)

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
        # customer allow only change to DRAFT, SUBMITTED and ACCEPT
        status = data.get('status', None)
        if status and status not in [DRAFT, SUBMITTED, ACCEPT]:
            raise serializers.ValidationError({'status': _("You can't perform this action.")})

        # update to ACCEPT must after DONE
        if instance and status == ACCEPT:
            if instance.status != DONE:
                raise serializers.ValidationError({'status': _("Purchase isn't finished yet.")})
            data['status'] = ACCEPT

        # prepare delivery data
        shipping_address = None
        shipping_address_uuid = data.pop('shipping_address_uuid', None)
        if shipping_address_uuid:
            try:
                shipping_address = ShippingAddress.objects.get(uuid=shipping_address_uuid)
            except ObjectDoesNotExist:
                raise serializers.ValidationError({'shipping_address': _("Invalid.")})

        schedule_date = data.pop('schedule_date', None)
        schedule_time_start = data.pop('schedule_time_start', None)
        schedule_time_end = data.pop('schedule_time_end', None)

        data['delivery_data'] = {
            'shipping_address': shipping_address,
            'schedule_date': schedule_date,
            'schedule_time_start': schedule_time_start,
            'schedule_time_end': schedule_time_end,
        }
        return data

    def to_representation(self, instance):
        """
        Serialize Purchase instances using a Purchase serializer,
        and note instances using a note serializer.
        """
        if isinstance(instance, Purchase):
            serializer = PurchaseSingleSerializer(instance, many=False, context=self.context)
        else:
            raise Exception(_("Unexpected type of object."))

        data = serializer.data
        if not getattr(data, 'has_delivery', None):
            data['has_delivery'] = instance.purchase_deliveries.exists()

        if not getattr(data, 'has_schedule', None):
            data['has_schedule'] = instance.purchase_deliveries \
                .filter(schedule_date__isnull=False,
                        schedule_time_start__isnull=False,
                        schedule_time_end__isnull=False) \
                .exists()
        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        status = validated_data.pop('status', None) # prevent user fill status
        delivery_data = validated_data.pop('delivery_data', None)
        shipping_address = delivery_data.get('shipping_address', None)

        obj = Purchase.objects.create(**validated_data, status=DRAFT)
        if obj and shipping_address:
            PurchaseDelivery.objects.create(purchase=obj, **delivery_data)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        # get and remove object
        delivery_data = validated_data.pop('delivery_data', None)
        shipping_address = delivery_data.get('shipping_address', None)

        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        # update or create shipping
        if shipping_address:
            if instance.purchase_deliveries.exists():
                current_deliveries = instance.purchase_deliveries \
                    .prefetch_related(Prefetch('purchase'), Prefetch('shipping_address')) \
                    .select_related('purchase', 'shipping_address') \
                    .all()

                current_deliveries.update(**delivery_data)
            else:
                PurchaseDelivery.objects.create(purchase=instance, **delivery_data)

        instance.save()
        return instance
