# Generated by Django 3.0.6 on 2020-05-22 22:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shoptask', '0020_auto_20200523_0534'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchasedelivery',
            name='shipping_to',
        ),
        migrations.AddField(
            model_name='purchasedelivery',
            name='shipping_address',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchase_deliveries', related_query_name='purchase_delivery', to='shoptask.ShippingAddress'),
        ),
    ]