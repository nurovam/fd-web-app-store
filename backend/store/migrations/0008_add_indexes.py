from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0007_order_status_received'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(db_index=True, decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='is_available',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
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
                db_index=True,
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
