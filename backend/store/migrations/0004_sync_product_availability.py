from django.db import migrations


def sync_availability(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    for product in Product.objects.all():
        is_available = product.stock_quantity > 0
        if product.is_available != is_available:
            product.is_available = is_available
            product.save(update_fields=['is_available'])


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0003_product_stock_quantity'),
    ]

    operations = [
        migrations.RunPython(sync_availability, migrations.RunPython.noop),
    ]
