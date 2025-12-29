from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Category, Product, Cart, CartItem


class CartSubtotalTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Инструменты")
        self.product = Product.objects.create(
            category=self.category,
            title="Тестовый товар",
            sku="SKU-1",
            price="100.00",
            inventory=10,
        )

    def test_cart_subtotal(self):
        cart = Cart.objects.create(session_key="test")
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(cart.subtotal, self.product.price * 2)
