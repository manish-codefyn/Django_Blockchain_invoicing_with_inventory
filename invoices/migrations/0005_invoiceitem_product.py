# Generated by Django 4.2.11 on 2025-05-12 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('invoices', '0004_alter_invoice_currency_alter_invoice_payment_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.product'),
        ),
    ]
