from django.conf import settings
from django.db import models
from django.db.models import Sum


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    is_available = models.BooleanField(default=True, db_index=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        needs_stock_sync = update_fields is None or bool({'stock_quantity', 'is_available'} & set(update_fields))
        if self.pk and needs_stock_sync and self.variants.exists():
            total = self.variants.aggregate(total=Sum('stock_quantity')).get('total') or 0
            self.stock_quantity = total
            self.is_available = total > 0
        elif needs_stock_sync:
            self.is_available = self.stock_quantity > 0
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=120, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = self.name
        if not label and self.attributes:
            label = ', '.join(f'{key}: {value}' for key, value in self.attributes.items())
        return label or f'Variant {self.id}'

    def save(self, *args, **kwargs):
        self.is_available = self.stock_quantity > 0
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.add('is_available')
            kwargs['update_fields'] = list(update_fields)
        super().save(*args, **kwargs)
        self.product.save(update_fields=['stock_quantity', 'is_available'])

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.save(update_fields=['stock_quantity', 'is_available'])


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    clinic_name = models.CharField(max_length=160, blank=True)

    def __str__(self):
        return self.full_name or self.user.username


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=80)
    line1 = models.CharField(max_length=160)
    line2 = models.CharField(max_length=160, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=120, default='Tajikistan')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.label} - {self.line1}'


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart({self.user.username})'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product', 'variant'],
                name='unique_cart_product_variant',
            ),
            models.UniqueConstraint(
                fields=['cart', 'product'],
                condition=models.Q(variant__isnull=True),
                name='unique_cart_product_no_variant',
            ),
        ]

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_RECEIVED = 'received'
    STATUS_CANCELED = 'canceled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_CANCELED, 'Canceled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f'Order({self.id}) - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=80, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reference = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment({self.order_id}) - {self.status}'


class ConsultationRequest(models.Model):
    STATUS_NEW = 'new'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_DONE, 'Done'),
    ]

    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40)
    message = models.TextField(blank=True)
    page_url = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    handled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'ConsultationRequest({self.id}) - {self.name}'
