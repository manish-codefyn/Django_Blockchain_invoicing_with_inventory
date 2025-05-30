# Generated by Django 4.2.11 on 2025-05-12 15:18

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('sku', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('tax_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('tax_included', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('stock_quantity', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('low_stock_threshold', models.DecimalField(decimal_places=2, default=10, max_digits=10)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProductStockMovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('movement_type', models.CharField(choices=[('purchase', 'Purchase'), ('sale', 'Sale'), ('adjustment', 'Adjustment'), ('return', 'Return'), ('transfer', 'Transfer')], max_length=20)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reference', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='products.product')),
            ],
            options={
                'verbose_name': 'Product Stock Movement',
                'verbose_name_plural': 'Product Stock Movements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductPriceHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('old_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('new_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('change_reason', models.TextField(blank=True)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='products.product')),
            ],
            options={
                'verbose_name': 'Product Price History',
                'verbose_name_plural': 'Product Price Histories',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Product Category',
                'verbose_name_plural': 'Product Categories',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.productcategory'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_products', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='product',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_products', to=settings.AUTH_USER_MODEL),
        ),
    ]
