from cart.models import Cart, Wishlist

def cart_and_wishlist_stats(request):
    cart_count = 0
    wishlist_count = 0
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.items.count()
            
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_count = wishlist.items.count()
            
    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }
