import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import ValidationError
from django.contrib.contenttypes.fields import GenericRelation

from utils.validators import IDENTIFIER_VALIDATOR, non_python_keyword
from apps.person.utils.constant import CUSTOMER
from apps.shoptask.utils.constant import DRAFT, SUBMITTED, STATUS_CHOICES, METRICS
from apps.shoptask.utils.log import CreateChangeLog

from django_currentuser.middleware import (
    get_current_user, get_current_authenticated_user)


class AbstractPurchase(models.Model):
    """
    each moment has different title
    like this;
    -------------
    belanja lebaran
    - kebutuhan dapur
    - kebutuhan bayi
    - ect
    """
    __original_status = None

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 limit_choices_to={
                                     'role__identifier': CUSTOMER
                                 },
                                 on_delete=models.CASCADE,
                                 related_name='purchases',
                                 related_query_name='purchase')

    label = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, max_length=255, null=True)
    description = models.TextField(blank=True)
    merchant = models.TextField(blank=True,
                                help_text=_("Who merchant prefered by Customer?"
                                            "Something like Alfamart at Paal Merah"))
    status = models.CharField(choices=STATUS_CHOICES, default=DRAFT,
                              validators=[IDENTIFIER_VALIDATOR,
                                          non_python_keyword],
                              max_length=255)

    class Meta:
        abstract = True
        verbose_name = _("Purchase")
        verbose_name_plural = _("Purchases")

    def __str__(self):
        return self.label

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_status = self.status

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        # create change log for status
        if self.status != self.__original_status:
            changelog = CreateChangeLog(
                obj=self,
                obj_id=self.id,
                column='status',
                old_value=self.__original_status,
                new_value=self.status
            ).save()

        super().save(force_insert, force_update, *args, **kwargs)
        self.__original_status = self.status

    @property
    def shipping(self):
        return self.purchase_deliveries.first()

    @property
    def assigned(self):
        return self.purchase_assigneds.first()


class AbstractNecessary(models.Model):
    """
    something goods has a classification
    like this;
    -------------
    belanja lebaran
    | -------------
    | kebutuhan dapur
    | - minyak <- this is Goods
    | - gula
    | -------------
    | kebutuhan bayi
    | - popok
    | - bedak
    | - minyak kayu putih
    | -------------
    | ect...
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 limit_choices_to={
                                     'role__identifier': CUSTOMER
                                 },
                                 on_delete=models.CASCADE,
                                 related_name='necessaries',
                                 related_query_name='necessary')
    purchase = models.ForeignKey('shoptask.Purchase',
                                 on_delete=models.CASCADE,
                                 related_name='necessaries',
                                 related_query_name='necessary')

    label = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, max_length=255, null=True)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True
        verbose_name = _("Necessary")
        verbose_name_plural = _("Necessaries")

    def __str__(self):
        return self.label


class AbstractGoods(models.Model):
    """
    :price is price of item
    :bill is total price x quantity
    -------------
    both filled by Operator, not customer
    -------------
    1 Pepsodent 300gr is IDR 3.000 with quantity 5 pack
    so bill is 3.000 x 5 = IDR 15.000
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 limit_choices_to={
                                     'role__identifier': CUSTOMER
                                 },
                                 on_delete=models.CASCADE,
                                 related_name='goods',
                                 related_query_name='goods')
    purchase = models.ForeignKey('shoptask.Purchase',
                                 on_delete=models.CASCADE,
                                 related_name='goods',
                                 related_query_name='goods',
                                 editable=False)
    necessary = models.ForeignKey('shoptask.Necessary',
                                  on_delete=models.CASCADE,
                                  related_name='goods',
                                  related_query_name='goods')

    label = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, max_length=255, null=True)
    description = models.TextField(blank=True)
    quantity = models.IntegerField()
    metric = models.CharField(choices=METRICS, max_length=255,
                              validators=[IDENTIFIER_VALIDATOR,
                                          non_python_keyword])
    price = models.BigIntegerField(blank=True, null=True)
    bill = models.BigIntegerField(blank=True, null=True)
    pictures = GenericRelation('shoptask.Attachment',
                               related_query_name='goods')

    class Meta:
        abstract = True
        verbose_name = _("Goods")
        verbose_name_plural = _("Goods")

    def save(self, *args, **kwargs):
        if self.necessary:
            self.purchase = self.necessary.purchase
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label


class AbstractGoodsExtraCharge(models.Model):
    """
    some Goods maybe has extra weight or dimension
    of cource need more extra power, time and place
    so we need also charge the extra
    but each Goods has different approach
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    goods = models.ForeignKey('shoptask.Goods', on_delete=models.CASCADE,
                              related_name='goods_extra_charges',
                              related_query_name='goods_extra_charge')
    extra_charge = models.ForeignKey('shoptask.ExtraCharge', on_delete=models.CASCADE,
                                     related_name='goods_extra_charges',
                                     related_query_name='goods_extra_charge')
    quantity = models.IntegerField()
    metric = models.CharField(max_length=255,
                              help_text=_("egg: Kilogram, Weight, etc"))
    charge = models.BigIntegerField(help_text=_("Total extra charge."))

    class Meta:
        abstract = True
        verbose_name = _("Goods Extra Charge")
        verbose_name_plural = _("Goods Extra Charges")

    def __str__(self):
        return self.goods.label


class AbstractGoodsCatalog(models.Model):
    """
    instead write-up Goods one-by-one
    easyly choice it from catalogs
    ------------
    each catalog selected its auto-filled the Goods field;
    - label
    - pictures
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    goods = models.OneToOneField('shoptask.Goods', on_delete=models.CASCADE,
                                 related_name='goods_catalogs',
                                 related_query_name='goods_catalog')
    catalog = models.ForeignKey('shoptask.Catalog', on_delete=models.CASCADE,
                                related_name='goods_catalogs',
                                related_query_name='goods_catalog')

    class Meta:
        abstract = True
        verbose_name = _("Goods Catalog")
        verbose_name_plural = _("Goods Catalogs")
        constraints = [
            models.UniqueConstraint(fields=['goods', 'catalog'],
                                    name='unique_goods_catalog')
        ]

    def __str__(self):
        return self.catalog.label
