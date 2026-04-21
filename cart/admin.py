from django.contrib import admin
from .models import Cart, CartItem, Wishlist, WishlistItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'created_at', 'total_price')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'session_id')
    inlines = [CartItemInline]

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0

class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__email',)
    inlines = [WishlistItemInline]

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(WishlistItem)
