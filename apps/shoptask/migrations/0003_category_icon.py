# Generated by Django 3.0.5 on 2020-05-01 01:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoptask', '0002_auto_20200501_0801'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.ImageField(blank=True, max_length=500, upload_to='images/icon'),
        ),
    ]
