# Generated by Django 3.0.6 on 2020-05-07 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoptask', '0004_auto_20200503_1944'),
    ]

    operations = [
        migrations.AddField(
            model_name='goodsassigned',
            name='is_skip',
            field=models.BooleanField(default=False),
        ),
    ]