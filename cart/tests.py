from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product, Category
from .models import Cart, CartItem, Wishlist, WishlistItem

User = get_user_model()

class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.category = Category.objects.create(name='Shoes', slug='shoes')
        self.product = Product.objects.create(
            name='Test Shoe',
            slug='test-shoe',
            price=100.00,
            category=self.category,
            is_active=True
        )

    def test_cart_creation(self):
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(str(cart), f"Cart - {self.user.email}")
        self.assertEqual(cart.total_price, 0)

    def test_cart_item_and_total_price(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(cart.total_price, 200.00)

class WishlistModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='wish@example.com', password='password')
        self.category = Category.objects.create(name='Shoes', slug='shoes-2')
        self.product = Product.objects.create(
            name='Cool Shoe',
            slug='cool-shoe',
            price=150.00,
            category=self.category,
            is_active=True
        )

    def test_wishlist_creation(self):
        wishlist = Wishlist.objects.create(user=self.user)
        self.assertEqual(str(wishlist), f"Wishlist - {self.user.email}")

    def test_wishlist_item(self):
        wishlist = Wishlist.objects.create(user=self.user)
        item = WishlistItem.objects.create(wishlist=wishlist, product=self.product)
        self.assertEqual(str(item), f"{self.product.name} in wishlist")
