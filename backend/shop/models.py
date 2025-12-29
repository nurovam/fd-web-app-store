from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class TimestampedModel(models.Model):
    """Reusable created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimestampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Product(TimestampedModel):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")
    inventory = models.PositiveIntegerField(default=0)
    hero_image = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.sku})"


class Cart(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="carts", null=True, blank=True, on_delete=models.CASCADE
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self) -> str:
        return f"Cart {self.pk}"

    @property
    def subtotal(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))


class CartItem(TimestampedModel):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"
        unique_together = ("cart", "product")

    def __str__(self) -> str:
        return f"{self.product.title} x {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return Decimal(self.quantity) * self.product.price


class Order(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        CREATED = "created", "Создан"
        PAID = "paid", "Оплачен"
        SHIPPED = "shipped", "Отгружен"
        CANCELLED = "cancelled", "Отменен"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk}"

    def recalculate_total(self) -> None:
        subtotal = sum((item.subtotal for item in self.items.all()), Decimal("0"))
        self.total = subtotal.quantize(Decimal("0.01"))
        self.save(update_fields=["total"])


class OrderItem(TimestampedModel):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    @property
    def subtotal(self) -> Decimal:
        return Decimal(self.quantity) * self.price


class ImportJob(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "В ожидании"
        COMPLETED = "completed", "Завершен"
        FAILED = "failed", "Ошибка"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="imports", on_delete=models.SET_NULL, null=True, blank=True
    )
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    processed_rows = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Импорт"
        verbose_name_plural = "Импорты"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Import {self.original_filename} ({self.status})"
