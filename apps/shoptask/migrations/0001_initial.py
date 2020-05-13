# Generated by Django 3.0.5 on 2020-04-29 06:18

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.files
import utils.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Goods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_updated', models.DateTimeField(auto_now=True, null=True)),
                ('label', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('amount', models.IntegerField()),
                ('metric', models.CharField(choices=[('kilogram', 'Kilogram'), ('hectogram', 'Ons'), ('gram', 'Gram'), ('pack', 'Bungkus'), ('piece', 'Buah'), ('bunch', 'Ikat'), ('sack', 'Karung / Sak'), ('unit', 'Unit')], max_length=255, validators=[django.core.validators.RegexValidator(message='Can only contain the letters a-z and underscores.', regex='^[a-zA-Z_][a-zA-Z_]*$'), utils.validators.non_python_keyword])),
                ('customer', models.ForeignKey(limit_choices_to={'role__identifier': 'customer'}, on_delete=django.db.models.deletion.CASCADE, related_name='goods', related_query_name='goods', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Goods',
                'verbose_name_plural': 'Goods',
                'db_table': 'shoptask_goods',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_updated', models.DateTimeField(auto_now=True, null=True)),
                ('label', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('needed_date', models.DateTimeField()),
                ('status', models.TextField(choices=[('submitted', 'Submitted'), ('reviewed', 'Reviewed'), ('accept', 'Accept'), ('assigned', 'Assigned'), ('processed', 'Processed'), ('done', 'Done')], default='submitted', max_length=255, validators=[django.core.validators.RegexValidator(message='Can only contain the letters a-z and underscores.', regex='^[a-zA-Z_][a-zA-Z_]*$'), utils.validators.non_python_keyword])),
                ('necessary_count', models.IntegerField(default=0, editable=False)),
                ('goods_count', models.IntegerField(default=0, editable=False)),
                ('customer', models.ForeignKey(limit_choices_to={'role__identifier': 'customer'}, on_delete=django.db.models.deletion.CASCADE, related_name='purchases', related_query_name='purchase', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Purchase',
                'verbose_name_plural': 'Purchases',
                'db_table': 'shoptask_purchase',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PurchaseAssigned',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_updated', models.DateTimeField(auto_now=True, null=True)),
                ('is_done', models.BooleanField(default=False)),
                ('is_accept', models.BooleanField(default=False)),
                ('operator', models.ForeignKey(limit_choices_to={'role__identifier': 'operator'}, on_delete=django.db.models.deletion.CASCADE, related_name='purchase_assigneds', related_query_name='purchase_assigned', to=settings.AUTH_USER_MODEL)),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchase_assigneds', related_query_name='purchase_assigned', to='shoptask.Purchase')),
            ],
            options={
                'verbose_name': 'Purchase Assigned',
                'verbose_name_plural': 'Purchase Assigneds',
                'db_table': 'shoptask_purchase_assigned',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Necessary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_updated', models.DateTimeField(auto_now=True, null=True)),
                ('label', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('goods_count', models.IntegerField(default=0, editable=False)),
                ('customer', models.ForeignKey(limit_choices_to={'role__identifier': 'customer'}, on_delete=django.db.models.deletion.CASCADE, related_name='necessaries', related_query_name='necessary', to=settings.AUTH_USER_MODEL)),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='necessaries', related_query_name='necessary', to='shoptask.Purchase')),
            ],
            options={
                'verbose_name': 'Necessary',
                'verbose_name_plural': 'Necessaries',
                'db_table': 'shoptask_necessary',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GoodsAssigned',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_updated', models.DateTimeField(auto_now=True, null=True)),
                ('is_done', models.BooleanField(default=False)),
                ('is_accept', models.BooleanField(default=False)),
                ('goods', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goods_assigneds', related_query_name='goods_assigned', to='shoptask.Goods')),
                ('operator', models.ForeignKey(limit_choices_to={'role__identifier': 'operator'}, on_delete=django.db.models.deletion.CASCADE, related_name='goods_assigneds', related_query_name='goods_assigned', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Goods Assigned',
                'verbose_name_plural': 'Goods Assigneds',
                'db_table': 'shoptask_goods_assigned',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='goods',
            name='necessary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goods', related_query_name='goods', to='shoptask.Necessary'),
        ),
        migrations.AddField(
            model_name='goods',
            name='purchase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goods', related_query_name='goods', to='shoptask.Purchase'),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('value_image', models.ImageField(blank=True, max_length=500, upload_to=utils.files.directory_image_path)),
                ('value_file', models.FileField(blank=True, max_length=500, upload_to=utils.files.directory_file_path)),
                ('identifier', models.CharField(blank=True, max_length=255, validators=[django.core.validators.RegexValidator(message='Can only contain the letters a-z and underscores.', regex='^[a-zA-Z_][a-zA-Z_]*$'), utils.validators.non_python_keyword])),
                ('caption', models.TextField(blank=True, max_length=500)),
                ('is_delete', models.BooleanField(default=False)),
                ('object_id', models.PositiveIntegerField(blank=True)),
                ('content_type', models.ForeignKey(blank=True, limit_choices_to=models.Q(app_label='shoptask'), on_delete=django.db.models.deletion.CASCADE, related_name='attachments', related_query_name='attachment', to='contenttypes.ContentType')),
                ('uploader', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attachments', related_query_name='attachment', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
                'db_table': 'shoptask_attachment',
                'ordering': ['-date_updated'],
                'abstract': False,
            },
        ),
    ]
