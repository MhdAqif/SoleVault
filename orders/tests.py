from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
import decimal
from products.models import Product, Category, Brand
from cart.models import Cart, CartItem
from orders.models import Coupon

User = get_user_model()

class CouponDiscountTest(TestCase):
    def setUp(self):
        # We need a user with email because standard fields are customized in settings
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="testpassword")
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.product = Product.objects.create(
            name="Expensive Shoe",
            slug="expensive-shoe",
            brand=self.brand,
            category=self.category,
            price=decimal.Decimal('15000.00'),
            image="test_image.jpg"
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        
    def test_percentage_coupon_with_limit(self):
        # 20% discount, max_discount = 2000
        coupon = Coupon.objects.create(
            code="SAVE20",
            discount_type="percentage",
            discount_value=decimal.Decimal("20.00"),
            min_spend=decimal.Decimal("1000.00"),
            max_discount=decimal.Decimal("2000.00"),
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_to=timezone.now() + datetime.timedelta(days=1),
            active=True
        )
        
        # 1. Test unit price 15,000, 20% = 3,000, should be capped at 2,000
        subtotal = decimal.Decimal("15000.00")
        items = [self.cart_item]
        discount = coupon.calculate_discount(subtotal, cart_items=items)
        self.assertEqual(discount, decimal.Decimal("2000.00"))
        
        # 2. Test fallback without cart_items (should still cap at 2000 overall)
        discount_fallback = coupon.calculate_discount(subtotal)
        self.assertEqual(discount_fallback, decimal.Decimal("2000.00"))

        # 3. Test quantity 2: unit price 15,000. Each unit gets 20% = 3,000 (capped at 2000). Total discount = 4,000.
        self.cart_item.quantity = 2
        self.cart_item.save()
        subtotal = decimal.Decimal("30000.00")
        discount_qty = coupon.calculate_discount(subtotal, cart_items=[self.cart_item])
        self.assertEqual(discount_qty, decimal.Decimal("4000.00"))

    def test_fixed_coupon(self):
        coupon = Coupon.objects.create(
            code="FLAT500",
            discount_type="fixed",
            discount_value=decimal.Decimal("500.00"),
            min_spend=decimal.Decimal("1000.00"),
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_to=timezone.now() + datetime.timedelta(days=1),
            active=True
        )
        subtotal = decimal.Decimal("15000.00")
        discount = coupon.calculate_discount(subtotal, cart_items=[self.cart_item])
        self.assertEqual(discount, decimal.Decimal("500.00"))
