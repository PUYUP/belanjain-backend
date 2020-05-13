import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from utils.validators import IDENTIFIER_VALIDATOR, non_python_keyword
from apps.shoptask.utils.constant import (
    DRAFT, CATALOG_STATUS, DIMENSION_METRICS, WEIGHT_METRICS,
    CATALOG_ATTRIBUTES, CATALOG_ATTRIBUTE_METRICS)


class AbstractCategory(models.Model):
    _UPLOAD_TO = 'images/icon'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True,
                               blank=True, related_name='categories',
                               related_query_name='category')
    label = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, max_length=255, null=True)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=1, blank=True)
    icon = models.ImageField(upload_to=_UPLOAD_TO, blank=True, max_length=500)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    catalog_count = models.IntegerField(editable=False, default=0)

    class Meta:
        abstract = True
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.label


class AbstractCatalog(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    category = models.ForeignKey('shoptask.Category', on_delete=models.SET_NULL,
                                 null=True, related_name='catalogs',
                                 related_query_name='catalog')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name='catalogs',
                             related_query_name='catalog')
    pictures = GenericRelation('shoptask.Attachment', related_query_name='catalog')

    sku = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, max_length=255, null=True)
    description = models.TextField(blank=True)
    status = models.CharField(choices=CATALOG_STATUS, default=DRAFT, max_length=255,
                              validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    is_delete = models.BooleanField(default=False)

    class Meta:
        abstract = True
        verbose_name = _("Catalog")
        verbose_name_plural = _("Catalogs")

    def __str__(self):
        return self.label


class AbstractCatalogAttribute(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    catalog = models.ForeignKey('shoptask.Catalog', on_delete=models.CASCADE,
                                related_name='catalog_attributes',
                                related_query_name='catalog_attribute')
    attribute = models.CharField(choices=CATALOG_ATTRIBUTES, max_length=255,
                                 validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    metric = models.CharField(choices=CATALOG_ATTRIBUTE_METRICS, max_length=255,
                              validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    value_text = models.CharField(_('Text'), blank=True, null=True, max_length=255)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True, db_index=True)
    value_boolean = models.NullBooleanField(_('Boolean'), blank=True, db_index=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        unique_together = ('attribute', 'catalog')
        verbose_name = _('Catalog Attribute')
        verbose_name_plural = _('Catalog Attributes')

    def __str__(self):
        return self.get_attribute_display()
