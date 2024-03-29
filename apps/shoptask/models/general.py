import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from utils.generals import get_model
from utils.files import directory_file_path, directory_image_path
from utils.validators import IDENTIFIER_VALIDATOR, non_python_keyword
from apps.person.utils.constant import CUSTOMER
from apps.shoptask.utils.constant import METRICS, DIMENSION_METRICS, WEIGHT_METRICS

_ALL_METRICS = METRICS + DIMENSION_METRICS + WEIGHT_METRICS


class AbstractAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # linked
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, related_name='attachments',
                                 related_query_name='attachment')

    # value
    value_image = models.ImageField(upload_to=directory_image_path, max_length=500,
                                    blank=True)
    value_file = models.FileField(upload_to=directory_file_path, max_length=500,
                                  blank=True)
    identifier = models.CharField(max_length=255, blank=True,
                                  validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    caption = models.TextField(max_length=500, blank=True)
    is_delete = models.BooleanField(default=False)

    # Generic relations
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     related_name='attachments',
                                     related_query_name='attachment',
                                     limit_choices_to=Q(app_label='shoptask'),
                                     blank=True)
    object_id = models.PositiveIntegerField(blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        ordering = ['-date_updated']
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    def __str__(self):
        value = None
        if self.value_image:
            value = self.value_image.url

        if self.value_file:
            value = self.value_file.url
        return value


class AbstractChangeLog(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    # Generic relations
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     related_name='changelogs',
                                     related_query_name='changelog',
                                     limit_choices_to=Q(app_label='shoptask'),
                                     blank=True)
    object_id = models.PositiveIntegerField(blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # values
    column = models.CharField(max_length=255)
    changed_date = models.DateTimeField(auto_now_add=True, null=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name='changelogs',
                                   related_query_name='changelog')
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['-date_created']
        verbose_name = _('Changelog')
        verbose_name_plural = _('Changelogs')

    def __str__(self):
        return self.new_value


class AbstractExtraCharge(models.Model):
    """
    for some Goods maybe has extra size and quantity
    example;
    Customer order 1 sack rice weight 10kg
    if order more than 1 of cource need extra power and place
    so we need to charge it
    ----------
    free for 1 sack @10kg and charge each 1kg extra if more than 1 sack
    :limit is tolerance before charged
    :charge is price for each 1 extra size
    ----------
    if :limit 1 sack and purchase goods.quantity is 2 sack = run extra charge
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    label = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255, help_text=_("Unique code."))
    excerpt = models.TextField(blank=True, max_length=255, null=True)
    description = models.TextField(blank=True)

    limit = models.IntegerField()
    metric = models.CharField(choices=_ALL_METRICS, max_length=255,
                              validators=[IDENTIFIER_VALIDATOR,
                                          non_python_keyword])
    charge = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ['-date_created']
        verbose_name = _('Extra Charge')
        verbose_name_plural = _('Extra Charges')

    def __str__(self):
        return self.label
