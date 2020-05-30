from django.apps import AppConfig
from django.db.models.signals import post_save


class ShoptaskConfig(AppConfig):
    name = 'apps.shoptask'

    def ready(self):
        from utils.generals import get_model
        from apps.shoptask.signals import purchase_save_handler, purchase_assigned_save_handler

        Purchase = get_model('shoptask', 'Purchase')
        PurchaseAssigned = get_model('shoptask', 'PurchaseAssigned')

        post_save.connect(purchase_save_handler, sender=Purchase,
                          dispatch_uid='purchase_save_signal')

        post_save.connect(purchase_assigned_save_handler, sender=PurchaseAssigned,
                          dispatch_uid='purchase_assigned_save_signal')
