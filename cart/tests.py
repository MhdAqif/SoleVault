from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product, Category
from cart.models import Cart, CartItem, Wishlist, WishlistItem

User = get_user_model()

class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test@example.com', email='test@example.com', password='password')
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
        self.user = User.objects.create_user(username='wish@example.com', email='wish@example.com', password='password')
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

class CartAjaxUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ajax@example.com', email='ajax@example.com', password='password')
        self.category = Category.objects.create(name='Shoes', slug='shoes')
        self.product = Product.objects.create(
            name='Test Shoe',
            slug='test-shoe',
            price=100.00,
            category=self.category,
            is_active=True
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_ajax_increase_quantity(self):
        self.client.login(email='ajax@example.com', password='password')
        # Simulate AJAX request to increase quantity
        response = self.client.post(
            f'/cart/update/{self.cart_item.id}/',
            {'action': 'increase'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['quantity'], 3)
        self.assertEqual(data['item_total_price'], 300.00)
        self.assertEqual(data['cart_total_price'], 300.00)

    def test_ajax_decrease_quantity(self):
        self.client.login(email='ajax@example.com', password='password')
        # Simulate AJAX request to decrease quantity
        response = self.client.post(
            f'/cart/update/{self.cart_item.id}/',
            {'action': 'decrease'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['quantity'], 1)
        self.assertEqual(data['item_total_price'], 100.00)
        self.assertEqual(data['cart_total_price'], 100.00)
