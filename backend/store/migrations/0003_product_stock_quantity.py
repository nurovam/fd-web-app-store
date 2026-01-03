from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_store_extensions'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
