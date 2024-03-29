# Generated by Django 3.0.6 on 2020-05-29 03:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shoptask', '0024_auto_20200529_0614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasedelivery',
            name='shipping_address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchase_deliveries', related_query_name='purchase_delivery', to='shoptask.ShippingAddress'),
        ),
        migrations.DeleteModel(
            name='PurchaseStatusChange',
        ),
    ]
