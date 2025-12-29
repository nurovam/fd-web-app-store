from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Category, Product, Cart, CartItem, Order, OrderItem, ImportJob

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image_url"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "sku",
            "description",
            "price",
            "currency",
            "inventory",
            "hero_image",
            "is_featured",
            "category",
            "category_id",
        ]

    def create(self, validated_data):
        category = validated_data.pop("category_id", None)
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        category = validated_data.pop("category_id", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.category = category or instance.category
        instance.save()
        return instance


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal"]
        read_only_fields = ["subtotal"]

    def create(self, validated_data):
        product = validated_data.pop("product_id")
        cart = self.context["cart"]
        item, _ = CartItem.objects.update_or_create(
            cart=cart, product=product, defaults={"quantity": validated_data.get("quantity", 1)}
        )
        return item

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "session_key", "items", "subtotal"]
        read_only_fields = ["user", "session_key", "subtotal"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_id", "quantity", "price", "subtotal"]
        read_only_fields = ["subtotal"]

    def create(self, validated_data):
        product = validated_data.pop("product_id")
        order = self.context["order"]
        return OrderItem.objects.create(order=order, product=product, **validated_data)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total",
            "shipping_address",
            "billing_address",
            "notes",
            "items",
            "created_at",
        ]
        read_only_fields = ["user", "status", "total", "created_at"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        order = Order.objects.create(user=self.context["request"].user, **validated_data)
        for item in items:
            serializer = OrderItemSerializer(data=item, context={"order": order})
            serializer.is_valid(raise_exception=True)
            serializer.save()
        order.recalculate_total()
        return order


class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportJob
        fields = [
            "id",
            "original_filename",
            "status",
            "processed_rows",
            "error_message",
            "report",
            "created_at",
        ]
