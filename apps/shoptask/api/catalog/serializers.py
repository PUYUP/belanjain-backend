from django.db import transaction
from django.db.models import Prefetch
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

Catalog = get_model('shoptask', 'Catalog')
Attachment = get_model('shoptask', 'Attachment')


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ('value_image',)


class CatalogSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='shoptask:catalog-detail', lookup_field='uuid',
        read_only=True)
    picture = serializers.SerializerMethodField(read_only=True)
    is_selected = serializers.BooleanField(read_only=True)

    class Meta:
        model = Catalog
        fields = ('id', 'uuid', 'label', 'url', 'picture', 'is_selected',)

    def get_picture(self, obj):
        request = self.context.get('request', None)
        if not request:
            raise NotAcceptable()

        picture = obj.pictures.first()
        if picture and picture.value_image:
            return request.build_absolute_uri(picture.value_image.url)
        return None


class CatalogSingleSerializer(serializers.ModelSerializer):
    pictures = AttachmentSerializer(many=True)

    class Meta:
        model = Catalog
        fields = '__all__'
