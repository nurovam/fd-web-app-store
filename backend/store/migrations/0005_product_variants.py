from django.db import migrations, models
import django.db.models.deletion
import django.db.models


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0004_sync_product_availability'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120)),
                ('attributes', models.JSONField(blank=True, default=dict)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('stock_quantity', models.PositiveIntegerField(default=0)),
                ('is_available', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='store.product')),
            ],
        ),
        migrations.AddField(
            model_name='cartitem',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='store.productvariant'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='store.productvariant'),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='cartitem',
            constraint=models.UniqueConstraint(fields=('cart', 'product', 'variant'), name='unique_cart_product_variant'),
        ),
        migrations.AddConstraint(
            model_name='cartitem',
            constraint=models.UniqueConstraint(condition=django.db.models.Q(variant__isnull=True), fields=('cart', 'product'), name='unique_cart_product_no_variant'),
        ),
    ]
