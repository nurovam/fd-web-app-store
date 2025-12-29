from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, ImportJob


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "sku", "category", "price", "inventory", "is_featured")
    search_fields = ("title", "sku")
    list_filter = ("category", "is_featured")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created_at")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total", "created_at")
    list_filter = ("status",)
    inlines = [OrderItemInline]


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "status", "processed_rows", "created_at")
    list_filter = ("status",)
