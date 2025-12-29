from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("image_url", models.URLField(blank=True)),
            ],
            options={
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="ImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("original_filename", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("pending", "В ожидании"), ("completed", "Завершен"), ("failed", "Ошибка")], default="pending", max_length=20)),
                ("processed_rows", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("report", models.JSONField(blank=True, default=dict)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="imports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Импорт",
                "verbose_name_plural": "Импорты",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("draft", "Черновик"), ("created", "Создан"), ("paid", "Оплачен"), ("shipped", "Отгружен"), ("cancelled", "Отменен")], default="created", max_length=20)),
                ("total", models.DecimalField(decimal_places=2, default="0", max_digits=12)),
                ("shipping_address", models.TextField(blank=True)),
                ("billing_address", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Заказ",
                "verbose_name_plural": "Заказы",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("sku", models.CharField(max_length=64, unique=True)),
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="RUB", max_length=8)),
                ("inventory", models.PositiveIntegerField(default=0)),
                ("hero_image", models.URLField(blank=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="shop.category")),
            ],
            options={
                "verbose_name": "Товар",
                "verbose_name_plural": "Товары",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shop.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="shop.product")),
            ],
            options={
                "verbose_name": "Позиция заказа",
                "verbose_name_plural": "Позиции заказа",
            },
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=64)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="carts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Корзина",
                "verbose_name_plural": "Корзины",
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("cart", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="shop.cart")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cart_items", to="shop.product")),
            ],
            options={
                "verbose_name": "Позиция корзины",
                "verbose_name_plural": "Позиции корзины",
                "unique_together": {("cart", "product")},
            },
        ),
    ]
