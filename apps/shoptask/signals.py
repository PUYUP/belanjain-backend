from utils.generals import get_model
from apps.shoptask.utils.constant import ASSIGNED, REVIEWED, ACCEPT

GoodsAssigned = get_model('shoptask', 'GoodsAssigned')


def purchase_save_handler(sender, instance, created, **kwargs):
    """
    Customer mark Purchase 'accept'
    then mark 'is_accept' in 'goods_assigneds' to True
    """
    if instance.status == ACCEPT:
        goods = instance.goods.filter(goods_assigned__isnull=False,
                                      goods_assigned__is_accept=False)
        if goods.exists():
            goods_assigned_update = list()
            for item in goods:
                assigned = item.goods_assigneds.first()
                if assigned:
                    assigned.is_accept = True
                goods_assigned_update.append(assigned)
            GoodsAssigned.objects.bulk_update(goods_assigned_update, ['is_accept'])


def purchase_assigned_save_handler(sender, instance, created, **kwargs):
    operator = getattr(instance, 'operator', None)
    purchase = getattr(instance, 'purchase', None)

    if purchase:
        if operator:
            purchase.status = ASSIGNED
        else:
            purchase.status = REVIEWED
        purchase.save()
