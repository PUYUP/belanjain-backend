from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_slug
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, ValidationError
from rest_framework.validators import UniqueTogetherValidator

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault
from apps.shoptask.utils.constant import DRAFT, SUBMITTED, DONE

from apps.person.api.user.serializers import SingleUserSerializer

Goods = get_model('shoptask', 'Goods')
GoodsCatalog = get_model('shoptask', 'GoodsCatalog')
GoodsAssigned = get_model('shoptask', 'GoodsAssigned')
Catalog = get_model('shoptask', 'Catalog')
Necessary = get_model('shoptask', 'Necessary')


class GoodsCatalogSerializer(serializers.ModelSerializer):
    default_metric = serializers.CharField(read_only=True, source='catalog.default_metric')
    # picture = serializers.ImageField(source='catalog.pictures.first.value_image', read_only=True)

    class Meta:
        model = GoodsCatalog
        fields = ('catalog', 'default_metric',)
        extra_kwargs = {'goods': {'read_only': True}}


class GoodsSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='customer:goods-detail', lookup_field='uuid',
        read_only=True)
    is_done = serializers.BooleanField(read_only=True)
    is_skip = serializers.BooleanField(read_only=True)
    is_accept = serializers.BooleanField(read_only=True)
    is_from_catalog = serializers.BooleanField(read_only=True)
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    picture = serializers.SerializerMethodField(read_only=True)
    goods_catalogs = GoodsCatalogSerializer()
    necessary_uuid = serializers.UUIDField(source='necessary.uuid', read_only=True)
    goods_assigned_uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Goods
        fields = ('id', 'uuid', 'label', 'url', 'is_done', 'is_skip', 'is_accept',
                  'is_from_catalog', 'quantity', 'metric', 'metric_display', 'price',
                  'description', 'necessary', 'necessary_uuid', 'goods_assigned_uuid',
                  'picture', 'goods_catalogs',)

    def get_picture(self, obj):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # Get image from Catalog if image from Goods not defined
        if not obj.pictures.exists():
            catalog_picture_path = obj.catalog_picture
            if catalog_picture_path:
                return request.build_absolute_uri(settings.MEDIA_URL + catalog_picture_path)
        return None


class GoodsSingleSerializer(serializers.ModelSerializer):
    is_done = serializers.BooleanField(read_only=True)
    is_skip = serializers.BooleanField(read_only=True)
    is_accept = serializers.BooleanField(read_only=True)
    is_from_catalog = serializers.BooleanField(read_only=True)
    
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    picture = serializers.SerializerMethodField(read_only=True)
    goods_catalogs = GoodsCatalogSerializer(read_only=True)

    class Meta:
        model = Goods
        fields = '__all__'

    def get_picture(self, obj):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # Get image from Catalog if image from Goods not defined
        if not obj.pictures.exists():
            goods_catalogs = getattr(obj, 'goods_catalogs', None)
            if goods_catalogs:
                catalog = getattr(goods_catalogs, 'catalog', None)
                catalog_picture_path = catalog.pictures.first()
                value_image = getattr(catalog_picture_path, 'value_image', None)
                if value_image:
                    return request.build_absolute_uri(value_image.url)
        return None


class GoodsFactorySerializer(serializers.ModelSerializer):
    """
    :label generated from Catalog name if create from Catalog
    """
    customer = serializers.HiddenField(default=CurrentUserDefault())
    catalog_uuid = serializers.UUIDField(required=False, write_only=True)
    necessary_uuid = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        model = Goods
        fields = ('label', 'description', 'quantity', 'metric',
                  'customer', 'necessary_uuid', 'catalog_uuid',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        data = kwargs.get('data', None)
        catalog_uuid = data.get('catalog_uuid', None)

        # If Catalog UUID present make `label` optional
        if catalog_uuid:
            self.fields['label'].required = False

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # extract `label` from Catalog, then put to required params
        catalog_uuid = data.pop('catalog_uuid', None)
        necessary_uuid = data.pop('necessary_uuid', None)

        if catalog_uuid:
             # Validate unique Goods and Catalog
            # Each Goods can't have multiple Catalog
            if GoodsCatalog.objects.filter(catalog__uuid=catalog_uuid,
                                           goods__necessary__uuid=necessary_uuid):
                raise serializers.ValidationError({
                    'goods_catalogs': _("Already exist.")})

            try:
                catalog = Catalog.objects.get(uuid=catalog_uuid)
                data['label'] = catalog.label
                data['catalog'] = catalog
            except ObjectDoesNotExist:
                raise serializers.ValidationError({
                    'catalog': _("Catalog param defined but invalid.")})

        if necessary_uuid:
            try:
                necessary = Necessary.objects.get(uuid=necessary_uuid)
                data['necessary'] = necessary
            except ObjectDoesNotExist:
                raise serializers.ValidationError({
                    'necessary': _("Necessary param defined but invalid.")})
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({'uuid': instance.uuid})
        data.update({'metric_display': instance.get_metric_display()})
        return data

    @transaction.atomic
    def create(self, validated_data):
        # get and exclude from instance attribute
        catalog = validated_data.pop('catalog', None)

        # create instance
        obj = Goods.objects.create(**validated_data)

        # User choice goods from catalog
        if obj and catalog:
            GoodsCatalog.objects.create(goods=obj, catalog=catalog)
        return obj

    @transaction.atomic
    def update(self, instance, validated_data):
        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        instance.save()
        return instance


class GoodsAssignedFactorySerializer(serializers.ModelSerializer):
    """
    :is_accept only customer can update
    """
    customer = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = GoodsAssigned
        fields = ('customer', 'is_accept',)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        instance = self.instance
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        # purchase status must at DONE to change is_accept assigned to True
        if instance.goods.purchase.status != DONE:
            raise serializers.ValidationError({
                'goods_assigned': _("Purchase not %s. This action can't perform." % DONE)})
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        # update the instance
        for item in validated_data:
            value = validated_data[item]
            setattr(instance, item, value)

        instance.save()
        return instance
