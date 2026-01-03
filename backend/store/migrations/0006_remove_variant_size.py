from django.db import migrations


def remove_variant_size(apps, schema_editor):
    ProductVariant = apps.get_model('store', 'ProductVariant')
    for variant in ProductVariant.objects.all().iterator():
        attributes = variant.attributes or {}
        if not isinstance(attributes, dict):
            continue
        if 'size' not in attributes:
            continue
        size_value = attributes.pop('size')
        name = (variant.name or '').strip()
        if not name and size_value not in (None, ''):
            name = str(size_value)
        ProductVariant.objects.filter(id=variant.id).update(
            name=name,
            attributes=attributes,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0005_product_variants'),
    ]

    operations = [
        migrations.RunPython(remove_variant_size, migrations.RunPython.noop),
    ]
