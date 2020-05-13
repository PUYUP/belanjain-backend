# Generated by Django 3.0.5 on 2020-05-03 12:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shoptask', '0003_category_icon'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchase',
            old_name='needed_date',
            new_name='schedule',
        ),
        migrations.AlterField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='categories', related_query_name='category', to='shoptask.Category'),
        ),
        migrations.AlterField(
            model_name='category',
            name='sort_order',
            field=models.IntegerField(blank=True, default=1),
        ),
        migrations.AlterField(
            model_name='shippingaddress',
            name='customer',
            field=models.ForeignKey(limit_choices_to={'role__identifier': 'customer'}, on_delete=django.db.models.deletion.CASCADE, related_name='shippings_address', related_query_name='shipping_address', to=settings.AUTH_USER_MODEL),
        ),
    ]
