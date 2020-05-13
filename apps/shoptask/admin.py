from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

# Register your models here.
from utils.generals import get_model

Attachment = get_model('shoptask', 'Attachment')
ChangeLog = get_model('shoptask', 'ChangeLog')
Purchase = get_model('shoptask', 'Purchase')
Necessary = get_model('shoptask', 'Necessary')
Goods = get_model('shoptask', 'Goods')
GoodsCatalog = get_model('shoptask', 'GoodsCatalog')
GoodsAssigned = get_model('shoptask', 'GoodsAssigned')
PurchaseAssigned = get_model('shoptask', 'PurchaseAssigned')
PurchaseShipping= get_model('shoptask', 'PurchaseShipping')

Category = get_model('shoptask', 'Category')
Catalog = get_model('shoptask', 'Catalog')
CatalogAttribute = get_model('shoptask', 'CatalogAttribute')
ShippingAddress = get_model('shoptask', 'ShippingAddress')


class AttachmentInline(GenericTabularInline):
    model = Attachment
    ct_fk_field = 'object_id'
    ct_field = 'content_type'


class CatalogAttributeInline(admin.StackedInline):
    model = CatalogAttribute


class CatalogExtend(admin.ModelAdmin):
    model = Catalog
    inlines = [AttachmentInline, CatalogAttributeInline,]


admin.site.register(ChangeLog)
admin.site.register(Attachment)

admin.site.register(Purchase)
admin.site.register(Necessary)
admin.site.register(Goods)
admin.site.register(GoodsCatalog)
admin.site.register(GoodsAssigned)
admin.site.register(PurchaseAssigned)
admin.site.register(PurchaseShipping)

admin.site.register(Category)
admin.site.register(Catalog, CatalogExtend)
admin.site.register(ShippingAddress)
