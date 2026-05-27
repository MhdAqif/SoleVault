from django.contrib import admin
from .models import Order, OrderItem, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'size', 'color', 'quantity', 'price', 'item_total', 'is_cancelled', 'cancel_reason']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'status', 'payment_status', 'final_price', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_id', 'user__email', 'full_name', 'phone']
    readonly_fields = ['order_id', 'user', 'subtotal', 'discount', 'tax', 'shipping_fee', 'final_price', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'min_spend', 'active', 'valid_from', 'valid_to']
    list_filter = ['active', 'discount_type', 'valid_from', 'valid_to']
    search_fields = ['code']
