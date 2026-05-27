from django.contrib import admin
from .models import Address, Wallet, WalletTransaction

admin.site.register(Address)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'updated_at']
    search_fields = ['user__email', 'user__first_name']

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'created_at', 'description']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__email', 'description']
