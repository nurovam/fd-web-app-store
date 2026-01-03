from django.contrib import admin
from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    ConsultationRequest,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductVariant,
    Profile,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_available')
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'stock_quantity', 'is_available', 'price')
    list_filter = ('is_available', 'product')
    search_fields = ('name', 'product__name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'clinic_name')
    search_fields = ('user__username', 'full_name', 'clinic_name')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'city', 'country', 'is_default')
    list_filter = ('country', 'is_default')
    search_fields = ('user__username', 'label', 'line1', 'city')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'provider', 'status', 'amount', 'created_at')
    list_filter = ('status', 'provider')


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'status', 'created_at', 'handled_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'message', 'page_url')
