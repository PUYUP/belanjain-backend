# Generated by Django 3.0.6 on 2020-05-13 02:33

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoptask', '0009_catalog_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='catalog',
            name='size_height',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_height_metric',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_length',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_length_metric',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_weight',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_weight_metric',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_width',
        ),
        migrations.RemoveField(
            model_name='catalog',
            name='size_width_metric',
        ),
        migrations.AddField(
            model_name='catalog',
            name='excerpt',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='excerpt',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='extracharge',
            name='excerpt',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='goods',
            name='excerpt',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='necessary',
            name='excerpt',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='purchase',
            name='excerpt',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='CatalogAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_updated', models.DateTimeField(auto_now=True, null=True)),
                ('attribute', models.CharField(choices=[('weight', 'Berat'), ('width', 'Panjang'), ('depth', 'Lebar'), ('height', 'Tinggi')], max_length=255, validators=[django.core.validators.RegexValidator(message='Can only contain the letters a-z and underscores.', regex='^[a-zA-Z_][a-zA-Z_]*$'), utils.validators.non_python_keyword])),
                ('metric', models.CharField(choices=[('kg', 'Kilogram'), ('hg', 'Ons'), ('g', 'Gram'), ('mg', 'Miligram'), ('pack', 'Bungkus'), ('piece', 'Buah'), ('bunch', 'Ikat'), ('sack', 'Karung / Sak'), ('unit', 'Unit'), ('kg', 'Kilogram'), ('hg', 'Ons'), ('g', 'Gram'), ('mg', 'Miligram'), ('km', 'Kilometer'), ('m', 'Meter'), ('cm', 'Sentimeter'), ('mm', 'Milimeter')], max_length=255, validators=[django.core.validators.RegexValidator(message='Can only contain the letters a-z and underscores.', regex='^[a-zA-Z_][a-zA-Z_]*$'), utils.validators.non_python_keyword])),
                ('value_text', models.CharField(blank=True, max_length=255, null=True, verbose_name='Text')),
                ('value_richtext', models.TextField(blank=True, null=True, verbose_name='Richtext')),
                ('value_integer', models.IntegerField(blank=True, db_index=True, null=True, verbose_name='Integer')),
                ('value_boolean', models.NullBooleanField(db_index=True, verbose_name='Boolean')),
                ('value_float', models.FloatField(blank=True, db_index=True, null=True, verbose_name='Float')),
                ('catalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='catalog_attributes', related_query_name='catalog_attribute', to='shoptask.Catalog')),
            ],
            options={
                'verbose_name': 'Catalog Attribute',
                'verbose_name_plural': 'Catalog Attributes',
                'db_table': 'shoptask_catalog_attribute',
                'abstract': False,
                'unique_together': {('attribute', 'catalog')},
            },
        ),
    ]
