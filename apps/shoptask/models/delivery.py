import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.generals import get_model
from apps.person.utils.constant import CUSTOMER


class AbstractShippingAddress(models.Model):
    """
    maybe a Customer has different shipping address
    more than one address
    ------------
    :is_default if checked the address default for Purchase address
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='shippings_address',
                                 related_query_name='shipping_address',
                                 limit_choices_to={
                                     'role__identifier': CUSTOMER
                                 })

    label = models.CharField(max_length=255, help_text=_("Eg; Home, Office, ect"))
    recipient = models.CharField(max_length=255, help_text=_("Eg; Abu Bakar Ash-Shiddiq"),
                                 blank=True)
    telephone = models.CharField(max_length=255)
    address = models.TextField(help_text=_("Complete address include number, building, street,"
                                           "province, district and other detail."))
    postal_code = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(blank=True, null=True, verbose_name=_("Latitude"))
    longitude = models.FloatField(blank=True, null=True, verbose_name=_("Longitude"))
    notes = models.TextField(blank=True, help_text=_("Eg; Put in garage"))
    is_default = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ['-date_created']
        verbose_name = _('Shipping Address')
        verbose_name_plural = _('Shippings Address')

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        # If current created set to is_default
        # Make old is_default to false
        if self.is_default:
            ShippingAddress = get_model('shoptask', 'ShippingAddress')
            old_objs = ShippingAddress.objects.filter(is_default=True, customer_id=self.customer.id)
            if old_objs.exists():
                old_objs.update(is_default=False)
        super().save(*args, **kwargs)


class AbstractPurchaseDelivery(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    schedule_date = models.DateField(blank=True, null=True)
    schedule_time_start = models.TimeField(blank=True, null=True)
    schedule_time_end = models.TimeField(blank=True, null=True)

    purchase = models.ForeignKey('shoptask.Purchase',
                                 on_delete=models.CASCADE,
                                 related_name='purchase_deliveries',
                                 related_query_name='purchase_delivery')
    shipping_address = models.ForeignKey('shoptask.ShippingAddress',
                                         on_delete=models.SET_NULL, null=True,
                                         related_name='purchase_deliveries',
                                         related_query_name='purchase_delivery')

    class Meta:
        abstract = True
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")

    def __str__(self):
        return self.shipping_address.label
