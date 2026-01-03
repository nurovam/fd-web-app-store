from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0006_remove_variant_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('paid', 'Paid'),
                    ('shipped', 'Shipped'),
                    ('received', 'Received'),
                    ('canceled', 'Canceled'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
