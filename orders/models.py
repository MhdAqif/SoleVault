from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('return_requested', 'Return Requested'),
        ('returned', 'Returned'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    order_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    # Shipping Address Snapshot
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    
    payment_method = models.CharField(max_length=50, default='COD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Razorpay Details
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    cancel_reason = models.TextField(blank=True, null=True)
    return_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id}"
        
    def save(self, *args, **kwargs):
        if not self.order_id:
            import datetime, random
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            random_digits = "".join([str(random.randint(0, 9)) for _ in range(4)])
            self.order_id = f"SV-{date_str}-{random_digits}"
            while Order.objects.filter(order_id=self.order_id).exists():
                random_digits = "".join([str(random.randint(0, 9)) for _ in range(4)])
                self.order_id = f"SV-{date_str}-{random_digits}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    product_name = models.CharField(max_length=250)
    size = models.CharField(max_length=50)
    color = models.CharField(max_length=50, blank=True)
    
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    is_cancelled = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True, null=True)
    return_status = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('requested', 'Return Requested'),
        ('approved', 'Returned/Approved'),
        ('rejected', 'Return Rejected')
    ], default='none')
    return_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.size}/{self.color}) in {self.order.order_id}"

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()}: {self.discount_value})"

    def is_valid(self, subtotal):
        from django.utils import timezone
        now = timezone.now()
        if not self.active:
            return False, "This coupon is no longer active."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon has expired."
        if subtotal < self.min_spend:
            return False, f"Minimum spend of ₹{self.min_spend} is required to apply this coupon."
        return True, ""

    def calculate_discount(self, subtotal, cart_items=None):
        if self.discount_type == 'fixed':
            return min(self.discount_value, subtotal)
        elif self.discount_type == 'percentage':
            import decimal
            if cart_items is not None:
                total_discount = decimal.Decimal('0.00')
                for item in cart_items:
                    unit_price = decimal.Decimal(str(item.product.offer_price))
                    unit_discount = unit_price * (self.discount_value / decimal.Decimal('100.00'))
                    if self.max_discount:
                        unit_discount = min(unit_discount, self.max_discount)
                    item_discount = unit_discount * item.quantity
                    total_discount += item_discount
                return total_discount
            else:
                discount = subtotal * (self.discount_value / decimal.Decimal('100.00'))
                if self.max_discount:
                    discount = min(discount, self.max_discount)
                return discount
        return decimal.Decimal('0.00')
