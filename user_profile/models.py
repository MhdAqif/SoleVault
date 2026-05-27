from django.db import models
from django.conf import settings

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} ({'Default' if self.is_default else 'Alternative'})"

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Wallet (₹{self.balance})"

class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} - ₹{self.amount} - {self.description}"