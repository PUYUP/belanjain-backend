from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, ValidationError
from rest_framework.validators import UniqueTogetherValidator

from utils.generals import get_model
from utils.validators import check_uuid
from apps.person.utils.auth import CurrentUserDefault
from apps.shoptask.utils.constant import DRAFT, SUBMITTED

from apps.shoptask.api.shipping.serializers import ShippingAddressSingleSerializer
from apps.person.api.user.serializers import SingleUserSerializer

Goods = get_model('shoptask', 'Goods')
GoodsCatalog = get_model('shoptask', 'GoodsCatalog')
Catalog = get_model('shoptask', 'Catalog')


class GoodsCatalogSerializer(serializers.ModelSerializer):
    default_metric = serializers.CharField(read_only=True, source='catalog.default_metric')
    # picture = serializers.ImageField(source='catalog.pictures.first.value_image', read_only=True)

    class Meta:
        model = GoodsCatalog
        fields = ('catalog', 'default_metric',)
        extra_kwargs = {'goods': {'read_only': True}}


class GoodsSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='shoptask:goods-detail', lookup_field='uuid',
        read_only=True)
    is_done = serializers.BooleanField(read_only=True)
    is_skip = serializers.BooleanField(read_only=True)
    is_accept = serializers.BooleanField(read_only=True)
    is_from_catalog = serializers.BooleanField(read_only=True)
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    picture = serializers.SerializerMethodField(read_only=True)
    goods_catalogs = GoodsCatalogSerializer()
    necessary_uuid = serializers.UUIDField(source='necessary.uuid', read_only=True)

    class Meta:
        model = Goods
        fields = ('id', 'uuid', 'label', 'url', 'is_done', 'is_skip', 'is_accept',
                  'is_from_catalog', 'quantity', 'metric', 'metric_display', 'price',
                  'description', 'necessary', 'necessary_uuid', 'picture', 'goods_catalogs',)

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
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    picture = serializers.SerializerMethodField(read_only=True)

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


class GoodsCreateSerializer(serializers.ModelSerializer):
    customer = serializers.HiddenField(default=CurrentUserDefault())
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    catalog_id = serializers.IntegerField(read_only=True)
    goods_catalogs = GoodsCatalogSerializer(required=False)

    class Meta:
        model = Goods
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        goods_catalogs = validated_data.pop('goods_catalogs', None)
        obj = Goods.objects.create(**validated_data)

         # User choice goods from catalog
        if goods_catalogs:
            catalog = goods_catalogs.get('catalog', None)
            necessary = validated_data.get('necessary', None)
        
            if obj and catalog:
                # Validate unique Goods and Catalog
                # Each Goods can't have multiple Catalog
                if GoodsCatalog.objects.filter(catalog=catalog, goods__necessary=necessary) \
                        .exclude(goods=obj).exists():
                    raise ValidationError(_("Catalog has selected in Goods."))
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
