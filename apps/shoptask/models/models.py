from .general import *
from .task import *
from .assign import *
from .product import *
from .delivery import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()

# 1
if not is_model_registered('shoptask', 'Purchase'):
    class Purchase(AbstractPurchase):
        class Meta(AbstractPurchase.Meta):
            db_table = 'shoptask_purchase'

    __all__.append('Purchase')


# 2
if not is_model_registered('shoptask', 'Necessary'):
    class Necessary(AbstractNecessary):
        class Meta(AbstractNecessary.Meta):
            db_table = 'shoptask_necessary'

    __all__.append('Necessary')


# 3
if not is_model_registered('shoptask', 'Goods'):
    class Goods(AbstractGoods):
        class Meta(AbstractGoods.Meta):
            db_table = 'shoptask_goods'

    __all__.append('Goods')


# 4
if not is_model_registered('shoptask', 'GoodsCatalog'):
    class GoodsCatalog(AbstractGoodsCatalog):
        class Meta(AbstractGoodsCatalog.Meta):
            db_table = 'shoptask_goods_catalog'

    __all__.append('GoodsCatalog')


# 5
if not is_model_registered('shoptask', 'PurchaseAssigned'):
    class PurchaseAssigned(AbstractPurchaseAssigned):
        class Meta(AbstractPurchaseAssigned.Meta):
            db_table = 'shoptask_purchase_assigned'

    __all__.append('PurchaseAssigned')


# 6
if not is_model_registered('shoptask', 'GoodsAssigned'):
    class GoodsAssigned(AbstractGoodsAssigned):
        class Meta(AbstractGoodsAssigned.Meta):
            db_table = 'shoptask_goods_assigned'

    __all__.append('GoodsAssigned')


# 7
if not is_model_registered('shoptask', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'shoptask_attachment'

    __all__.append('Attachment')


# 8
if not is_model_registered('shoptask', 'ChangeLog'):
    class ChangeLog(AbstractChangeLog):
        class Meta(AbstractChangeLog.Meta):
            db_table = 'shoptask_changelog'

    __all__.append('ChangeLog')


# 9
if not is_model_registered('shoptask', 'Category'):
    class Category(AbstractCategory):
        class Meta(AbstractCategory.Meta):
            db_table = 'shoptask_category'

    __all__.append('Category')


# 10
if not is_model_registered('shoptask', 'Brand'):
    class Brand(AbstractBrand):
        class Meta(AbstractBrand.Meta):
            db_table = 'shoptask_brand'

    __all__.append('Brand')


# 11
if not is_model_registered('shoptask', 'Catalog'):
    class Catalog(AbstractCatalog):
        class Meta(AbstractCatalog.Meta):
            db_table = 'shoptask_catalog'

    __all__.append('Catalog')


# 12
if not is_model_registered('shoptask', 'CatalogAttribute'):
    class CatalogAttribute(AbstractCatalogAttribute):
        class Meta(AbstractCatalogAttribute.Meta):
            db_table = 'shoptask_catalog_attribute'

    __all__.append('CatalogAttribute')


# 13
if not is_model_registered('shoptask', 'ShippingAddress'):
    class ShippingAddress(AbstractShippingAddress):
        class Meta(AbstractShippingAddress.Meta):
            db_table = 'shoptask_shipping_address'

    __all__.append('ShippingAddress')


# 14
if not is_model_registered('shoptask', 'PurchaseDelivery'):
    class PurchaseDelivery(AbstractPurchaseDelivery):
        class Meta(AbstractPurchaseDelivery.Meta):
            db_table = 'shoptask_purchase_delivery'

    __all__.append('PurchaseDelivery')


# 15
if not is_model_registered('shoptask', 'ExtraCharge'):
    class ExtraCharge(AbstractExtraCharge):
        class Meta(AbstractExtraCharge.Meta):
            db_table = 'shoptask_extra_charge'

    __all__.append('ExtraCharge')


# 16
if not is_model_registered('shoptask', 'GoodsExtraCharge'):
    class GoodsExtraCharge(AbstractGoodsExtraCharge):
        class Meta(AbstractGoodsExtraCharge.Meta):
            db_table = 'shoptask_goods_extra_charge'

    __all__.append('GoodsExtraCharge')
