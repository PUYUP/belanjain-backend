import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import ValidationError

from apps.person.utils.constant import OPERATOR, CUSTOMER


class AbstractPurchaseAssigned(models.Model):
    """
    :is_done marked by Operator
    :is_accept marked by Purchaser
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    purchase = models.ForeignKey('shoptask.Purchase',
                                 on_delete=models.CASCADE,
                                 related_name='purchase_assigneds',
                                 related_query_name='purchase_assigned')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 limit_choices_to={
                                     'role__identifier': OPERATOR
                                 },
                                 on_delete=models.CASCADE,
                                 related_name='purchase_assigneds',
                                 related_query_name='purchase_assigned')

    is_done = models.BooleanField(default=False)
    is_accept = models.BooleanField(default=False)

    class Meta:
        abstract = True
        verbose_name = _("Purchase Assigned")
        verbose_name_plural = _("Purchase Assigneds")

    def clean(self):
        roles = self.operator.roles.all().values_list('identifier', flat=True)

        if self.is_accept and OPERATOR in roles:
            raise ValidationError(_("Action restricted."))

    def save(self, *args, **kwargs):
        customer = self.purchase.customer
        if customer:
            self.customer = customer
        super().save(*args, **kwargs)

    def __str__(self):
        return self.purchase.label


class AbstractGoodsAssigned(models.Model):
    """
    :is_skip market by Operator
    :is_done marked by Operator
    :is_accept marked by Customer
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    goods = models.ForeignKey('shoptask.Goods',
                              on_delete=models.CASCADE,
                              related_name='goods_assigneds',
                              related_query_name='goods_assigned')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 limit_choices_to={
                                     'role__identifier': OPERATOR
                                 },
                                 on_delete=models.CASCADE,
                                 related_name='goods_assigneds',
                                 related_query_name='goods_assigned')

    is_skip = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)
    is_accept = models.BooleanField(default=False)

    class Meta:
        abstract = True
        verbose_name = _("Goods Assigned")
        verbose_name_plural = _("Goods Assigneds")

    def save(self, *args, **kwargs):
        customer = self.goods.customer
        if customer:
            self.customer = customer
        super().save(*args, **kwargs)

    def __str__(self):
        return self.goods.label
