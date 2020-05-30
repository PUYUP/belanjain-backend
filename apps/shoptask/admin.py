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
PurchaseDelivery= get_model('shoptask', 'PurchaseDelivery')

Category = get_model('shoptask', 'Category')
Brand = get_model('shoptask', 'Brand')
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
    list_display = ('label', 'default_metric',)
    inlines = [AttachmentInline, CatalogAttributeInline,]


class GoodsCatalogInline(admin.StackedInline):
    model = GoodsCatalog


class GoodsExtend(admin.ModelAdmin):
    model = Goods
    inlines = [GoodsCatalogInline,]


admin.site.register(ChangeLog)
admin.site.register(Attachment)

admin.site.register(Purchase)
admin.site.register(Necessary)
admin.site.register(Goods, GoodsExtend)
admin.site.register(GoodsCatalog)
admin.site.register(GoodsAssigned)
admin.site.register(PurchaseAssigned)
admin.site.register(PurchaseDelivery)

admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Catalog, CatalogExtend)
admin.site.register(ShippingAddress)
